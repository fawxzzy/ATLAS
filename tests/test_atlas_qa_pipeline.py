from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import urllib.parse
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from PIL import Image

from ops.atlas.qa.baselines import bless_baseline, propose_baselines
from ops.atlas.qa.bootstrap_adapter_repo import bootstrap_adapter_repo
from ops.atlas.qa.ci_gate import _materialize_runtime_waivers, _provider_override_file, _provider_status, _wait_for_url
from ops.atlas.qa.adoption_drift import build_adoption_drift
from ops.atlas.qa.bootstrap_release_repos import bootstrap_release_repos
from ops.atlas.qa.compatibility_report import compatibility_report
from ops.atlas.qa.collect_artifacts import _capture_cache
from ops.atlas.qa.evidence_index import build_evidence_index
from ops.atlas.qa.evaluate_run import evaluate_run
from ops.atlas.qa.github_secret_readiness import github_secret_readiness
from ops.atlas.qa.manual_attestation import (
    build_manual_attestation_packet_prep,
    scaffold_manual_attestations,
    validate_attestations_for_run,
)
from ops.atlas.qa.provider_readiness import provider_readiness
from ops.atlas.qa.release_gate_packet import build_release_gate_packet
from ops.atlas.qa.promote_run import promote_run
from ops.atlas.qa.protected_release_refresh import refresh_protected_release_receipts
from ops.atlas.qa.release_snapshot import build_release_snapshot
from ops.atlas.qa.release_rehearsal import build_release_rehearsal
from ops.atlas.qa.release_readiness import build_release_readiness
from ops.atlas.qa.report_run import report_run
from ops.atlas.qa.run_matrix import run_matrix
from ops.atlas.qa.test_evidence import collect_test_evidence
from ops.atlas.qa.waiver_monitor import build_waiver_monitor
from ops.atlas.qa.visual_diff import evaluate_visual_diffs
from ops.atlas.qa._common import (
    build_receipt_origin,
    load_json_object,
    validate_adapter_manifest,
    validate_provider_manifest,
    validate_scenario_manifest,
)
from ops.atlas.qa.providers import capture_with_provider
from ops.atlas.qa.validate_artifacts import validate_artifact_manifest_file
from ops.cortex._artifacts import sha256_bytes, write_json
from ops.validation.validate_stack import build_findings, validate_declared_surface_scan_coverage

ROOT = Path(__file__).resolve().parents[1]


def _png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (8, 8), (0, 128, 255, 255)).save(path, format="PNG")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _init_committed_repo(path: Path, *, filename: str = "README.md", content: str = "# repo\n") -> str:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.email", "atlas-test@example.com")
    _git(path, "config", "user.name", "ATLAS Test")
    (path / filename).write_text(content, encoding="utf-8")
    _git(path, "add", filename)
    _git(path, "commit", "-m", "init")
    return _git(path, "rev-parse", "HEAD")


def _write_repo_inventory(root: Path, *, repos: list[dict]) -> None:
    _write_json(
        root / "docs" / "registry" / "STACK-REPO-INVENTORY.json",
        {
            "schema_version": "atlas.stack.repo-inventory.v1",
            "repos": repos,
            "excluded_surfaces": [],
        },
    )


def _write_waiver(
    *,
    root: Path,
    run_id: str = "run-1",
    repo_id: str = "fitness",
    scenario_id: str = "fitness.progression-pr-smoke",
    waived_lane: str = "android.chrome.real.manual",
    expires_at: str = "2099-01-01T00:00:00Z",
) -> Path:
    waiver_path = root / "runtime" / "atlas" / "qa" / "runs" / run_id / "waivers" / f"{waived_lane}.waiver.json"
    _write_json(
        waiver_path,
        {
            "contract_version": "atlas.qa.waiver.v1",
            "waiver_id": f"{run_id}:{waived_lane}:waiver",
            "repo_id": repo_id,
            "scenario_id": scenario_id,
            "run_id": run_id,
            "waived_lane": waived_lane,
            "reason": "Android device/provider unavailable in current operator environment",
            "operator": "atlas-operator",
            "operator_identity": "local:test",
            "created_at": "2026-05-12T00:00:00Z",
            "expires_at": expires_at,
            "evidence_present": [
                "desktop.chromium.real.manual",
                "iphone.webkit.real.manual",
                "android.chrome.emulated"
            ],
            "limitation": "Android physical proof was not captured"
        },
    )
    return waiver_path


def _manual_attestation(
    *,
    root: Path,
    screenshot: Path,
    run_id: str = "run-1",
    storage_run_id: str = "run-1",
    expires_at: str = "2099-01-01T00:00:00Z",
) -> Path:
    attestation_path = root / "runtime" / "atlas" / "qa" / "runs" / storage_run_id / "manual-attestations" / "iphone.manual.json"
    _write_json(
        attestation_path,
        {
            "contract_version": "atlas.qa.manual_attestation.v1",
            "attestation_id": "att-1",
            "operator": "atlas-operator",
            "operator_identity": "local:test",
            "scenario_id": "fitness.progression-pr-smoke",
            "adapter_id": "fitness.web",
            "run_id": run_id,
            "lens_id": "iphone.webkit.real",
            "device_model": "iPhone 15",
            "os_name": "iOS",
            "os_version": "17.5",
            "browser_name": "Safari",
            "browser_version": "17.5",
            "capture_timestamp": "2026-05-11T00:00:00Z",
            "expires_at": expires_at,
            "screenshot_artifacts": [
                {
                    "path_ref": "runtime/atlas/qa/runs/run-1/captures/iphone.webkit.real/manual.png",
                    "checksum_sha256": sha256_bytes(screenshot.read_bytes()),
                }
            ],
            "notes": ["manual attestation fixture"],
        },
    )
    return attestation_path


class AtlasQaPipelineTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "runtime" / "atlas" / "qa" / "runs" / "run-1").mkdir(parents=True, exist_ok=True)
        (root / "schemas").mkdir(parents=True, exist_ok=True)
        (root / "stack.yaml").write_text(
            "\n".join(
                [
                    "repo_registry:",
                    "  fitness:",
                    "    path: repos/fawxzzy-fitness",
                    "    role: app",
                    "    status: active",
                    "  foundation:",
                    "    path: repos/fawxzzy-foundation",
                    "    role: package",
                    "    status: active",
                    "  lifeline:",
                    "    path: repos/lifeline",
                    "    role: package",
                    "    status: active",
                    "  playbook:",
                    "    path: repos/fawxzzy-playbook",
                    "    role: docs",
                    "    status: active",
                    "  trove:",
                    "    path: repos/fawxzzy-trove",
                    "    role: app",
                    "    status: active",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        for schema_name in (
            "atlas.qa.promotion.v1.json",
            "atlas.qa.waiver.v1.json",
            "atlas.qa.capture_receipt.v1.json",
            "atlas.qa.visual_baseline.v1.json",
            "atlas.qa.adapter.v1.json",
            "atlas.qa.artifact.v1.json",
            "atlas.qa.result.v1.json",
            "atlas.qa.scenario.v1.json",
            "atlas.qa.test_evidence.v1.json",
            "atlas.qa.evidence_index.v1.json",
        ):
            (root / "schemas" / schema_name).write_text(
                (ROOT / "schemas" / schema_name).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        (root / "README-STACK.md").write_text("# temp\n", encoding="utf-8")
        (root / "AGENTS.md").write_text("# temp\n", encoding="utf-8")
        (root / "docs").mkdir(exist_ok=True)
        (root / "ops").mkdir(exist_ok=True)
        (root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        return root

    def _write_baseline_manifest(self, *, root: Path, baseline_path: Path, lens_id: str, state: str = "blessed", artifact_hash: str | None = None) -> Path:
        manifest_path = baseline_path.with_suffix(".baseline.json")
        _write_json(
            manifest_path,
            {
                "contract_version": "atlas.qa.visual_baseline.v1",
                "baseline_id": "sha256:" + ("b" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "scenario_id": "fitness.progression-pr-smoke",
                "adapter_id": "fitness.web",
                "lens_id": lens_id,
                "evidence_tier": "emulated_browser",
                "source_run_id": "run-1",
                "git_sha": "abcdef1234567890",
                "artifact_hash": artifact_hash or sha256_bytes(baseline_path.read_bytes()),
                "state": state,
                "baseline_ref": str(baseline_path.relative_to(root).as_posix()),
                "candidate_image_ref": "runtime/atlas/qa/runs/run-1/captures/desktop.chromium.emulated/screenshot.png",
                "approved_by": "atlas-test",
                "approved_at": "2026-05-11T00:00:00Z",
            },
        )
        return manifest_path

    def _write_stack_lock(self, *, root: Path, components: dict[str, str]) -> None:
        lines = [
            'schema_version: "atlas.stack.lock.v1"',
            "components:",
        ]
        for repo_id, commit in components.items():
            lines.append(f"  {repo_id}:")
            lines.append(f'    commit: "{commit}"')
        (root / "stack.lock.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _base_manifest(self, *, root: Path) -> tuple[Path, Path]:
        screenshot = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / "desktop.chromium.emulated" / "screenshot.png"
        _png(screenshot)
        digest = sha256_bytes(screenshot.read_bytes())
        manifest = {
            "contract_version": "atlas.qa.artifact.v1",
            "artifact_manifest_id": "sha256:" + ("1" * 64),
            "generated_at": "2026-05-11T00:00:00Z",
            "run_id": "run-1",
            "scenario_id": "fitness.progression-pr-smoke",
            "adapter_id": "fitness.web",
            "repo_id": "fitness",
            "repo_path": "repos/fawxzzy-fitness",
            "stage": "collected",
            "mode": "execute",
            "evidence_grade": "evidence",
            "git_sha": "abcdef1234567890",
            "environment": {
                "execution_root": "runtime/atlas/qa/runs/run-1",
                "target_url": "http://127.0.0.1:3000/dev/mobile-regression"
            },
            "lenses": {
                "desktop.chromium": {
                    "browser_engine": "chromium",
                    "viewport": {
                        "width": 1440,
                        "height": 1024,
                        "device_scale_factor": 1
                    },
                    "mobile": False,
                    "has_touch": False
                }
            },
            "artifacts": [
                {
                    "artifact_id": "run-1:main:desktop.chromium.emulated:screenshot",
                    "artifact_kind": "screenshot",
                    "step_id": "main",
                    "lens_id": "desktop.chromium.emulated",
                    "proof_kind": "emulated",
                    "required": True,
                    "status": "present",
                    "path_ref": "runtime/atlas/qa/runs/run-1/captures/desktop.chromium.emulated/screenshot.png",
                    "content_type": "image/png",
                    "checksum_sha256": digest,
                    "evidence": {
                        "run_id": "run-1",
                        "scenario_id": "fitness.progression-pr-smoke",
                        "adapter_id": "fitness.web",
                        "repo_id": "fitness",
                        "git_sha": "abcdef1234567890",
                        "lens_id": "desktop.chromium.emulated",
                        "viewport": {
                            "width": 1440,
                            "height": 1024,
                            "device_scale_factor": 1,
                            "mobile": False
                        },
                        "browser_engine": "chromium",
                        "captured_at": "2026-05-11T00:00:00Z",
                        "source_url": "http://127.0.0.1:3000/dev/mobile-regression",
                        "artifact_sha256": digest,
                        "evidence_tier": "emulated_browser",
                        "capture_method": "browser_emulation",
                        "capture_backend": "playwright",
                        "metadata_ref": "runtime/atlas/qa/runs/run-1/captures/desktop.chromium.emulated/capture.metadata.json"
                    },
                    "notes": []
                }
            ],
            "summary": {
                "artifact_count": 1,
                "required_count": 1,
                "present_count": 1,
                "missing_count": 0,
                "manual_required_count": 0,
                "invalid_count": 0
            }
        }
        manifest_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "artifacts.manifest.json"
        _write_json(manifest_path, manifest)
        return manifest_path, screenshot

    def test_missing_screenshot_fails_validation(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        screenshot.unlink()
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=False)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] == "missing_artifact_file" for item in report["findings"]))

    def test_zero_byte_screenshot_fails_validation(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        screenshot.write_bytes(b"")
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=False)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] == "zero_byte_artifact" for item in report["findings"]))

    def test_bootstrap_adapter_repo_clones_exact_sha_from_inventory_remote(self) -> None:
        root = self._temp_root()
        remote_repo = root / "tmp-remote-fitness"
        commit = _init_committed_repo(remote_repo, content="# fitness\n")
        (root / "ops" / "atlas" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        _write_json(
            root / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json",
            {
                "contract_version": "atlas.qa.adapter.v1",
                "adapter_id": "fitness.web",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "framework": "nextjs",
                "commands": {
                    "verify": {
                        "command": "npm run verify",
                    }
                },
                "prepare": {
                    "kind": "command",
                    "command": "npm install",
                },
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "lenses": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "profile_id": "desktop.chromium",
                        "proof_kind": "emulated",
                        "evidence_kind": "emulated_browser",
                        "required_for": ["evidence"],
                        "promotion_tier": "emulated_browser",
                        "fallback_behavior": "blocked",
                        "execution_mode": "browser_capture",
                    }
                ],
            },
        )
        (root / "ops" / "atlas" / "qa" / "lenses").mkdir(parents=True, exist_ok=True)
        _write_json(
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            {
                "contract_version": "atlas.qa.lens_manifest.v1",
                "lenses": [
                    {"lens_id": "desktop.chromium"},
                ],
            },
        )
        _write_repo_inventory(
            root,
            repos=[
                {
                    "logical_id": "fitness",
                    "local_path": "repos/fawxzzy-fitness",
                    "remote_url": str(remote_repo.resolve()),
                    "current_commit": commit,
                }
            ],
        )

        result = bootstrap_adapter_repo(root=root, adapter="fitness.web", target_sha=commit)
        self.assertEqual(commit, result["checkout_sha"])
        self.assertTrue((root / result["bootstrap_adapter_repo_ref"]).exists())
        self.assertEqual(commit, _git(root / "repos" / "fawxzzy-fitness", "rev-parse", "HEAD"))

    def test_declared_surface_scan_coverage_accepts_required_surfaces(self) -> None:
        root = self._temp_root()
        findings = validate_declared_surface_scan_coverage(root, {"repo_registry": {}}, root / "stack.yaml")
        self.assertEqual([], findings)

    def test_declared_surface_scan_coverage_flags_missing_required_surface(self) -> None:
        root = self._temp_root()
        real_collect = validate_declared_surface_scan_coverage.__globals__["collect_text_scan_roots"]

        def _missing_docs(*args, **kwargs):
            roots = real_collect(*args, **kwargs)
            docs_path = (root / "docs").resolve()
            return [item for item in roots if item.resolve() != docs_path]

        with mock.patch("ops.validation.validate_stack.collect_text_scan_roots", side_effect=_missing_docs):
            findings = validate_declared_surface_scan_coverage(root, {"repo_registry": {}}, root / "stack.yaml")
        self.assertTrue(any(item.category == "declared-scan-surface-missing" and item.path == "docs" for item in findings))

    def test_build_findings_allows_missing_locked_repos_in_sparse_mode(self) -> None:
        root = self._temp_root()
        (root / "stack.yaml").write_text(
            "\n".join(
                [
                    "repo_registry:",
                    "  stack:",
                    "    path: .",
                    "    role: operator-layer",
                    "    status: active",
                    "  _stack:",
                    "    path: repos/_stack",
                    "    role: workflow-operator",
                    "    status: active",
                    "  playbook:",
                    "    path: repos/fawxzzy-playbook",
                    "    role: governance-runtime",
                    "    status: active",
                    "  foundation:",
                    "    path: repos/fawxzzy-foundation",
                    "    role: package",
                    "    status: active",
                    "stack_lock:",
                    "  include_repo_ids:",
                    "    - stack",
                    "    - _stack",
                    "    - playbook",
                    "    - foundation",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        _git(root, "init")
        _git(root, "config", "user.email", "atlas-test@example.com")
        _git(root, "config", "user.name", "ATLAS Test")
        _git(root, "add", "README-STACK.md", "AGENTS.md", "stack.yaml")
        _git(root, "commit", "-m", "init")
        playbook_repo = root / "repos" / "fawxzzy-playbook"
        playbook_commit = _init_committed_repo(playbook_repo, content="# playbook\n")
        (playbook_repo / "AGENTS.md").write_text("# playbook\n", encoding="utf-8")
        (playbook_repo / ".codex").mkdir(exist_ok=True)
        (playbook_repo / ".codex" / "config.toml").write_text("model = 'gpt-5.4'\n", encoding="utf-8")
        (root / "stack.lock.yaml").write_text(
            "\n".join(
                [
                    'schema_version: "atlas.stack.lock.v1"',
                    'stack_manifest_path: "stack.yaml"',
                    'stack_manifest_digest: "sha256:' + ("a" * 64) + '"',
                    "component_count: 4",
                    "components:",
                    "  stack:",
                    '    path: "."',
                    '    role: "operator-layer"',
                    '    status: "active"',
                    "    remote: null",
                    '    ref_type: "branch"',
                    '    ref: "main"',
                    '    commit: "' + ("e" * 40) + '"',
                    "    dirty: true",
                    '    trust_class: "trusted"',
                    "    release_eligible: false",
                    "  _stack:",
                    '    path: "repos/_stack"',
                    '    role: "workflow-operator"',
                    '    status: "active"',
                    "    remote: null",
                    '    ref_type: "branch"',
                    '    ref: "main"',
                    '    commit: "' + ("1" * 40) + '"',
                    "    dirty: false",
                    '    trust_class: "trusted"',
                    "    release_eligible: false",
                    "  playbook:",
                    '    path: "repos/fawxzzy-playbook"',
                    '    role: "governance-runtime"',
                    '    status: "active"',
                    "    remote: null",
                    '    ref_type: "branch"',
                    '    ref: "main"',
                    f'    commit: "{playbook_commit}"',
                    "    dirty: false",
                    '    trust_class: "trusted"',
                    "    release_eligible: true",
                    "  foundation:",
                    '    path: "repos/fawxzzy-foundation"',
                    '    role: "package"',
                    '    status: "active"',
                    "    remote: null",
                    '    ref_type: "branch"',
                    '    ref: "main"',
                    '    commit: "' + ("2" * 40) + '"',
                    "    dirty: false",
                    '    trust_class: "trusted"',
                    "    release_eligible: true",
                    "excluded_surfaces: {}",
                    'lock_digest: "sha256:' + ("b" * 64) + '"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        findings = build_findings(
            root / "stack.yaml",
            json.loads(json.dumps({"repo_registry": {
                "stack": {"path": ".", "role": "operator-layer", "status": "active"},
                "_stack": {"path": "repos/_stack", "role": "workflow-operator", "status": "active"},
                "playbook": {"path": "repos/fawxzzy-playbook", "role": "governance-runtime", "status": "active"},
                "foundation": {"path": "repos/fawxzzy-foundation", "role": "package", "status": "active"},
            }, "stack_lock": {"include_repo_ids": ["stack", "_stack", "playbook", "foundation"]}})),
            allow_missing_locked_repos=True,
            required_present_repo_ids={"playbook"},
        )
        categories = {(item.category, item.path) for item in findings}
        self.assertNotIn(("missing-repo-path", "repos/_stack"), categories)
        self.assertNotIn(("missing-repo-path", "repos/fawxzzy-foundation"), categories)
        self.assertFalse(any(item.category in {"stack-lock-build-failed", "stack-lock-drift"} for item in findings))

    def test_build_findings_sparse_mode_skips_runtime_state_and_detached_ref_checks(self) -> None:
        root = self._temp_root()
        (root / "stack.yaml").write_text(
            "\n".join(
                [
                    "repo_registry:",
                    "  stack:",
                    "    path: .",
                    "    role: operator-layer",
                    "    status: active",
                    "  playbook:",
                    "    path: repos/fawxzzy-playbook",
                    "    role: governance-runtime",
                    "    status: active",
                    "  fitness:",
                    "    path: repos/fawxzzy-fitness",
                    "    role: application",
                    "    status: active",
                    "paths:",
                    "  tmp: tmp",
                    "  secrets: secrets",
                    "subpaths:",
                    "  runtime:",
                    "    state: runtime/state",
                    "    receipts: runtime/receipts",
                    "stack_lock:",
                    "  include_repo_ids:",
                    "    - stack",
                    "    - playbook",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        _git(root, "init")
        _git(root, "config", "user.email", "atlas-test@example.com")
        _git(root, "config", "user.name", "ATLAS Test")
        _git(root, "add", "README-STACK.md", "AGENTS.md", "stack.yaml")
        _git(root, "commit", "-m", "init")
        playbook_repo = root / "repos" / "fawxzzy-playbook"
        playbook_commit = _init_committed_repo(playbook_repo, content="# playbook\n")
        (playbook_repo / "AGENTS.md").write_text("# playbook\n", encoding="utf-8")
        _git(playbook_repo, "checkout", "--detach", playbook_commit)
        stack_commit = _git(root, "rev-parse", "HEAD")
        (root / "stack.lock.yaml").write_text(
            "\n".join(
                [
                    'schema_version: "atlas.stack.lock.v1"',
                    'stack_manifest_path: "stack.yaml"',
                    'stack_manifest_digest: "sha256:' + ("c" * 64) + '"',
                    "component_count: 2",
                    "components:",
                    "  stack:",
                    '    path: "."',
                    '    role: "operator-layer"',
                    '    status: "active"',
                    "    remote: null",
                    '    ref_type: "branch"',
                    '    ref: "main"',
                    f'    commit: "{stack_commit}"',
                    "    dirty: false",
                    '    trust_class: "trusted"',
                    "    release_eligible: false",
                    "  playbook:",
                    '    path: "repos/fawxzzy-playbook"',
                    '    role: "governance-runtime"',
                    '    status: "active"',
                    "    remote: null",
                    '    ref_type: "branch"',
                    '    ref: "main"',
                    f'    commit: "{playbook_commit}"',
                    "    dirty: false",
                    '    trust_class: "trusted"',
                    "    release_eligible: true",
                    "excluded_surfaces: {}",
                    'lock_digest: "sha256:' + ("d" * 64) + '"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        config = json.loads(
            json.dumps(
                {
                    "repo_registry": {
                        "stack": {"path": ".", "role": "operator-layer", "status": "active"},
                        "playbook": {"path": "repos/fawxzzy-playbook", "role": "governance-runtime", "status": "active"},
                        "fitness": {"path": "repos/fawxzzy-fitness", "role": "application", "status": "active"},
                    },
                    "paths": {"tmp": "tmp", "secrets": "secrets"},
                    "subpaths": {"runtime": {"state": "runtime/state", "receipts": "runtime/receipts"}},
                    "stack_lock": {"include_repo_ids": ["stack", "playbook"]},
                }
            )
        )
        with (
            mock.patch("ops.validation.validate_stack.validate_declared_surface_scan_coverage", return_value=[]),
            mock.patch("ops.validation.validate_stack.validate_atlas_topology_contract_files", return_value=(0, "", [])),
            mock.patch("ops.validation.validate_stack.validate_tool_registry", return_value=[]),
            mock.patch("ops.validation.validate_stack.validate_subsystem_registry", return_value=[]),
            mock.patch("ops.validation.validate_stack.validate_playbook_enforcement_tracking", return_value=[]),
            mock.patch("ops.validation.validate_stack.validate_execution_receipt_repairs", side_effect=AssertionError("sparse mode should skip execution receipt repair validation")),
            mock.patch("ops.validation.validate_stack.validate_verta_trust_gate", side_effect=AssertionError("sparse mode should skip Verta trust-gate validation")),
            mock.patch("ops.validation.validate_stack.validate_working_memory", side_effect=AssertionError("sparse mode should skip working-memory validation")),
            mock.patch("ops.validation.validate_stack.validate_world_model_state", side_effect=AssertionError("sparse mode should skip world-model validation")),
            mock.patch("ops.validation.validate_stack.validate_proposed_sessions", side_effect=AssertionError("sparse mode should skip proposed session validation")),
        ):
            findings = build_findings(
                root / "stack.yaml",
                config,
                allow_missing_locked_repos=True,
                required_present_repo_ids={"playbook"},
            )
        categories = {(item.category, item.path) for item in findings}
        self.assertNotIn(("missing-directory", "tmp"), categories)
        self.assertNotIn(("missing-directory", "secrets"), categories)
        self.assertNotIn(("missing-directory", "runtime/state"), categories)
        self.assertNotIn(("missing-directory", "runtime/receipts"), categories)
        self.assertNotIn(("missing-repo-path", "repos/fawxzzy-fitness"), categories)
        self.assertNotIn(("missing-codex-config", "repos/fawxzzy-playbook"), categories)
        self.assertNotIn(("stack-lock-missing-ref", "stack.lock.yaml#playbook"), categories)
        self.assertNotIn(("stack-lock-missing-ref", "stack.lock.yaml#stack"), categories)

    def test_invalid_image_file_fails_validation(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        screenshot.write_bytes(b"not-a-png")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifacts"][0]["checksum_sha256"] = sha256_bytes(b"not-a-png")
        manifest["artifacts"][0]["evidence"]["artifact_sha256"] = sha256_bytes(b"not-a-png")
        _write_json(manifest_path, manifest)
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=False)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] == "invalid_image_file" for item in report["findings"]))

    def test_wrong_run_id_fails_validation(self) -> None:
        root = self._temp_root()
        manifest_path, _ = self._base_manifest(root=root)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifacts"][0]["evidence"]["run_id"] = "wrong-run"
        _write_json(manifest_path, manifest)
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=False)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] == "wrong_run_id" for item in report["findings"]))

    def test_missing_artifact_hash_fails_validation(self) -> None:
        root = self._temp_root()
        manifest_path, _ = self._base_manifest(root=root)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifacts"][0]["evidence"]["artifact_sha256"] = ""
        _write_json(manifest_path, manifest)
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=False)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] in {"missing_evidence_field", "missing_artifact_hash"} for item in report["findings"]))

    def test_dry_run_artifact_is_not_promotion_grade(self) -> None:
        root = self._temp_root()
        manifest_path, _ = self._base_manifest(root=root)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["mode"] = "dry_run"
        manifest["evidence_grade"] = "dry_run"
        _write_json(manifest_path, manifest)
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=True)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] == "dry_run_evidence" for item in report["findings"]))

    def test_provider_automation_screenshot_receipt_validates(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifacts"][0]["lens_id"] = "android.chrome.real"
        manifest["artifacts"][0]["proof_kind"] = "real"
        manifest["artifacts"][0]["artifact_id"] = "run-1:main:android.chrome.real:screenshot"
        manifest["artifacts"][0]["evidence"]["lens_id"] = "android.chrome.real"
        manifest["artifacts"][0]["evidence"]["capture_method"] = "provider_automation"
        manifest["artifacts"][0]["evidence"]["evidence_tier"] = "physical_device"
        manifest["artifacts"][0]["evidence"]["provider_id"] = "mock.physical-device"
        manifest["artifacts"][0]["evidence"]["provider_run_id"] = "mock-run"
        manifest["artifacts"][0]["evidence"]["device_model"] = "Pixel 8"
        manifest["artifacts"][0]["evidence"]["os_name"] = "Android"
        manifest["artifacts"][0]["evidence"]["os_version"] = "14"
        manifest["artifacts"][0]["evidence"]["browser_name"] = "Chrome"
        metadata_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / "desktop.chromium.emulated" / "capture.metadata.json"
        _write_json(
            metadata_path,
            {
                "contract_version": "atlas.qa.capture_receipt.v1",
                "run_id": "run-1",
                "scenario_id": "fitness.progression-pr-smoke",
                "adapter_id": "fitness.web",
                "repo_id": "fitness",
                "git_sha": "abcdef1234567890",
                "lens_id": "android.chrome.real",
                "captured_at": "2026-05-11T00:00:00Z",
                "source_url": "http://127.0.0.1:3000/dev/mobile-regression",
                "capture_backend": "mock-provider",
                "capture_method": "provider_automation"
            },
        )
        manifest["artifacts"][0]["evidence"]["metadata_ref"] = "runtime/atlas/qa/runs/run-1/captures/desktop.chromium.emulated/capture.metadata.json"
        _write_json(manifest_path, manifest)
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=True)
        self.assertEqual("clean", report["status"])

    def test_manual_attestation_wrong_run_id_fails_validation(self) -> None:
        root = self._temp_root()
        screenshot = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / "iphone.webkit.real" / "manual.png"
        _png(screenshot)
        attestation_path = _manual_attestation(root=root, screenshot=screenshot, run_id="wrong-run")
        manifest = {
            "contract_version": "atlas.qa.artifact.v1",
            "artifact_manifest_id": "sha256:" + ("3" * 64),
            "generated_at": "2026-05-11T00:00:00Z",
            "run_id": "run-1",
            "scenario_id": "fitness.progression-pr-smoke",
            "adapter_id": "fitness.web",
            "repo_id": "fitness",
            "repo_path": "repos/fawxzzy-fitness",
            "stage": "collected",
            "mode": "execute",
            "evidence_grade": "evidence",
            "git_sha": "abcdef1234567890",
            "environment": {"execution_root": "runtime/atlas/qa/runs/run-1", "target_url": "http://127.0.0.1:3000"},
            "lenses": {
                "iphone.webkit": {
                    "browser_engine": "webkit",
                    "viewport": {"width": 393, "height": 852, "device_scale_factor": 3},
                    "mobile": True,
                    "has_touch": True,
                }
            },
            "attestations": [
                {
                    "attestation_id": "att-1",
                    "attestation_ref": "runtime/atlas/qa/runs/run-1/manual-attestations/iphone.manual.json",
                    "run_id": "wrong-run",
                    "scenario_id": "fitness.progression-pr-smoke",
                    "adapter_id": "fitness.web",
                    "lens_id": "iphone.webkit.real",
                    "operator": "atlas-operator",
                    "capture_method": "manual_attestation",
                    "status": "valid",
                }
            ],
            "artifacts": [
                {
                    "artifact_id": "run-1:main:iphone.webkit.real:trace",
                    "artifact_kind": "trace",
                    "step_id": "main",
                    "lens_id": "iphone.webkit.real",
                    "proof_kind": "real",
                    "required": True,
                    "status": "manual_attested",
                    "source_ref": "runtime/atlas/qa/runs/run-1/manual-attestations/iphone.manual.json",
                }
            ],
            "summary": {
                "artifact_count": 1,
                "required_count": 1,
                "present_count": 0,
                "missing_count": 0,
                "manual_required_count": 0,
                "manual_attested_count": 1,
                "invalid_count": 0,
            },
        }
        manifest_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "artifacts.manifest.json"
        _write_json(manifest_path, manifest)
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=True)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] == "attestation_wrong_run_id" for item in report["findings"]))

    def test_stale_manual_attestation_fails_validation(self) -> None:
        root = self._temp_root()
        screenshot = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / "iphone.webkit.real" / "manual.png"
        _png(screenshot)
        _manual_attestation(root=root, screenshot=screenshot, expires_at="2000-01-01T00:00:00Z")
        manifest = {
            "contract_version": "atlas.qa.artifact.v1",
            "artifact_manifest_id": "sha256:" + ("4" * 64),
            "generated_at": "2026-05-11T00:00:00Z",
            "run_id": "run-1",
            "scenario_id": "fitness.progression-pr-smoke",
            "adapter_id": "fitness.web",
            "repo_id": "fitness",
            "repo_path": "repos/fawxzzy-fitness",
            "stage": "collected",
            "mode": "execute",
            "evidence_grade": "evidence",
            "git_sha": "abcdef1234567890",
            "environment": {"execution_root": "runtime/atlas/qa/runs/run-1", "target_url": "http://127.0.0.1:3000"},
            "lenses": {
                "iphone.webkit": {
                    "browser_engine": "webkit",
                    "viewport": {"width": 393, "height": 852, "device_scale_factor": 3},
                    "mobile": True,
                    "has_touch": True,
                }
            },
            "attestations": [
                {
                    "attestation_id": "att-1",
                    "attestation_ref": "runtime/atlas/qa/runs/run-1/manual-attestations/iphone.manual.json",
                    "run_id": "run-1",
                    "scenario_id": "fitness.progression-pr-smoke",
                    "adapter_id": "fitness.web",
                    "lens_id": "iphone.webkit.real",
                    "operator": "atlas-operator",
                    "capture_method": "manual_attestation",
                    "status": "valid",
                }
            ],
            "artifacts": [],
            "summary": {
                "artifact_count": 0,
                "required_count": 0,
                "present_count": 0,
                "missing_count": 0,
                "manual_required_count": 0,
                "manual_attested_count": 0,
                "invalid_count": 0,
            },
        }
        manifest_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "artifacts.manifest.json"
        _write_json(manifest_path, manifest)
        report = validate_artifact_manifest_file(root=root, artifact_path=manifest_path, promotion_strict=True)
        self.assertEqual("invalid", report["status"])
        self.assertTrue(any(item["code"] == "stale_attestation" for item in report["findings"]))

    def test_promote_run_marks_dry_run_status(self) -> None:
        root = self._temp_root()
        result_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "evaluated.result.json"
        artifact_path, _ = self._base_manifest(root=root)
        scenario_path = root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            scenario_path,
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "title": "fixture",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "adapter_id": "fitness.web",
                "criticality": "high",
                "entrypoint": {"path": "/"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": [],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "preview_only"
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": [], "certify_command_sequence": []},
                "promotion": {
                    "require_executable_truth": True,
                    "require_pr_artifacts": True,
                    "require_real_device_on": "release",
                    "allow_manual_certification": True,
                    "max_flaky_lenses": 0
                }
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            {
                "contract_version": "atlas.qa.lens.v1",
                "lens_set_id": "atlas-default-web",
                "title": "fixture",
                "lenses": [
                    {
                        "lens_id": "desktop.chromium",
                        "browser_engine": "chromium",
                        "viewport": {"width": 1, "height": 1, "device_scale_factor": 1},
                        "mobile": False,
                        "has_touch": False
                    }
                ]
            },
        )
        _write_json(
            result_path,
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("2" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "dry_run",
                "summary": {
                    "overall_status": "dry_run",
                    "executable_status": "planned",
                    "artifact_status": "planned",
                    "certification_status": "planned",
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": []
            },
        )
        promotion = promote_run(root=root, result_path=result_path, artifact_path=artifact_path, scenario_path=scenario_path)
        self.assertEqual("dry_run", promotion["promotion_status"])

    def test_promote_run_marks_manual_attested_physical_status(self) -> None:
        root = self._temp_root()
        result_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "evaluated.result.json"
        artifact_path, _ = self._base_manifest(root=root)
        scenario_path = root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            scenario_path,
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "title": "fixture",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "adapter_id": "fitness.web",
                "criticality": "high",
                "entrypoint": {"path": "/"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": ["iphone.webkit.real"],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "preview_only"
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": [], "certify_command_sequence": []},
                "promotion": {
                    "require_executable_truth": True,
                    "require_pr_artifacts": True,
                    "require_real_device_on": "release",
                    "allow_manual_certification": True,
                    "max_flaky_lenses": 0
                }
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            {
                "contract_version": "atlas.qa.lens.v1",
                "lens_set_id": "atlas-default-web",
                "title": "fixture",
                "lenses": [
                    {
                        "lens_id": "desktop.chromium",
                        "browser_engine": "chromium",
                        "viewport": {"width": 1, "height": 1, "device_scale_factor": 1},
                        "mobile": False,
                        "has_touch": False
                    }
                ]
            },
        )
        _write_json(
            result_path,
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("6" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_attested",
                    "highest_satisfied_tier": "manual_attestation",
                    "satisfied_evidence_tiers": ["emulated_browser", "manual_attestation"],
                    "missing_evidence_tiers": [],
                    "manual_required_lanes": [],
                    "lens_count": 2,
                    "failing_lens_count": 0,
                    "finding_count": 0
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": []
            },
        )
        promotion = promote_run(root=root, result_path=result_path, artifact_path=artifact_path, scenario_path=scenario_path)
        self.assertEqual("promoted_physical_manual", promotion["promotion_status"])

    def test_promote_run_applies_lane_scoped_waiver_without_marking_android_passed(self) -> None:
        root = self._temp_root()
        result_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "evaluated.result.json"
        artifact_path, _ = self._base_manifest(root=root)
        scenario_path = root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            scenario_path,
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "title": "fixture",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "adapter_id": "fitness.web",
                "criticality": "high",
                "entrypoint": {"path": "/"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": ["desktop.chromium.real", "iphone.webkit.real", "android.chrome.real"],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "preview_only"
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": [], "certify_command_sequence": []},
                "promotion": {
                    "require_executable_truth": True,
                    "require_pr_artifacts": True,
                    "require_real_device_on": "release",
                    "allow_manual_certification": True,
                    "max_flaky_lenses": 0
                }
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            {
                "contract_version": "atlas.qa.lens.v1",
                "lens_set_id": "atlas-default-web",
                "title": "fixture",
                "lenses": [
                    {
                        "lens_id": "desktop.chromium",
                        "browser_engine": "chromium",
                        "viewport": {"width": 1, "height": 1, "device_scale_factor": 1},
                        "mobile": False,
                        "has_touch": False
                    }
                ]
            },
        )
        _write_json(
            result_path,
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("6" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "manual_attestation",
                    "satisfied_evidence_tiers": ["emulated_browser", "manual_attestation"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["desktop.chromium.real", "iphone.webkit.real", "android.chrome.real"],
                    "lens_count": 4,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                    "visual_status": "passed",
                    "test_evidence_status": "clean"
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": []
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "manual_attestation.result.json",
            {
                "runner_version": "atlas.qa.manual-attestation.validate.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "run_id": "run-1",
                "status": "invalid",
                "attestation_count": 3,
                "attestations": [
                    {"lens_id": "desktop.chromium.real", "status": "valid"},
                    {"lens_id": "iphone.webkit.real", "status": "valid"},
                    {"lens_id": "android.chrome.real", "status": "invalid"},
                ],
                "finding_count": 1,
                "findings": [{"severity": "error", "code": "missing_attestation_screenshot", "message": "android missing"}],
            },
        )
        _write_waiver(root=root, run_id="run-1")
        promotion = promote_run(root=root, result_path=result_path, artifact_path=artifact_path, scenario_path=scenario_path)
        self.assertEqual("waived_promoted", promotion["promotion_status"])
        self.assertEqual("waived", promotion["summary"]["real_device_proof"])
        self.assertEqual(["android.chrome.real.manual"], promotion["waived_lanes"])
        self.assertEqual([], promotion["manual_required_lanes"])

    def test_evaluate_run_carries_manual_required_artifact_lanes_into_promotion(self) -> None:
        root = self._temp_root()
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / "run-1"
        artifact_path, _ = self._base_manifest(root=root)
        scenario_path = root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            scenario_path,
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "title": "fixture",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "adapter_id": "fitness.web",
                "criticality": "high",
                "entrypoint": {"path": "/"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": ["iphone.webkit.real"],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "preview_only",
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": [], "certify_command_sequence": []},
                "promotion": {
                    "require_executable_truth": True,
                    "require_pr_artifacts": True,
                    "require_real_device_on": "release",
                    "allow_manual_certification": True,
                    "max_flaky_lenses": 0,
                },
            },
        )
        _write_json(
            run_root / "matrix.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("6" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "executed",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "satisfied",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": [],
                    "visual_status": "not_configured",
                    "visual_diff_count": 0,
                    "test_evidence_status": "not_configured",
                    "required_test_evidence_count": 0,
                    "lens_count": 2,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "lens_profile_id": "desktop.chromium",
                        "proof_kind": "emulated",
                        "evidence_kind": "emulated_browser",
                        "promotion_tier": "emulated_browser",
                        "fallback_behavior": "blocked",
                        "execution_mode": "browser_capture",
                        "status": "pass",
                    },
                    {
                        "lens_id": "iphone.webkit.real",
                        "lens_profile_id": "iphone.webkit",
                        "proof_kind": "real",
                        "evidence_kind": "physical_device",
                        "promotion_tier": "physical_device",
                        "fallback_behavior": "manual_attestation",
                        "execution_mode": "provider_capture",
                        "status": "pass",
                    },
                ],
                "findings": [],
                "artifact_manifest_refs": [],
            },
        )
        artifact_payload = load_json_object(artifact_path)
        artifact_payload["artifacts"].append(
            {
                "artifact_id": "run-1:main:iphone.webkit.real:screenshot",
                "artifact_kind": "screenshot",
                "step_id": "main",
                "lens_id": "iphone.webkit.real",
                "proof_kind": "real",
                "required": True,
                "status": "manual_required",
                "content_type": "image/png",
                "notes": [],
            }
        )
        artifact_payload["summary"]["artifact_count"] = 2
        artifact_payload["summary"]["required_count"] = 2
        artifact_payload["summary"]["manual_required_count"] = 1
        _write_json(artifact_path, artifact_payload)
        _write_json(
            run_root / "captures" / "desktop.chromium.emulated" / "capture.metadata.json",
            {
                "contract_version": "atlas.qa.capture_receipt.v1",
                "run_id": "run-1",
                "scenario_id": "fitness.progression-pr-smoke",
                "adapter_id": "fitness.web",
                "repo_id": "fitness",
                "git_sha": "abcdef1234567890",
                "lens_id": "desktop.chromium.emulated",
                "captured_at": "2026-05-11T00:00:00Z",
                "source_url": "http://127.0.0.1:3000/dev/mobile-regression",
                "capture_backend": "playwright",
                "capture_method": "browser_emulation",
            },
        )

        evaluated = evaluate_run(root=root, run_id="run-1")
        self.assertEqual("manual_required", evaluated["summary"]["certification_status"])
        self.assertEqual(["iphone.webkit.real"], evaluated["summary"]["manual_required_lanes"])

        promotion = promote_run(root=root, run_id="run-1", scenario_path=scenario_path)
        self.assertEqual("manual_review", promotion["promotion_status"])
        self.assertEqual("manual_required", promotion["summary"]["real_device_proof"])
        self.assertEqual(["iphone.webkit.real"], promotion["manual_required_lanes"])

    def test_promote_run_rejects_wrong_run_waiver(self) -> None:
        root = self._temp_root()
        result_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "evaluated.result.json"
        artifact_path, _ = self._base_manifest(root=root)
        scenario_path = root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            scenario_path,
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "title": "fixture",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "adapter_id": "fitness.web",
                "criticality": "high",
                "entrypoint": {"path": "/"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": ["android.chrome.real.manual"],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "preview_only"
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": [], "certify_command_sequence": []},
                "promotion": {"require_real_device_on": "release", "allow_manual_certification": True}
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            {
                "contract_version": "atlas.qa.lens.v1",
                "lens_set_id": "atlas-default-web",
                "title": "fixture",
                "lenses": [
                    {
                        "lens_id": "desktop.chromium",
                        "browser_engine": "chromium",
                        "viewport": {"width": 1, "height": 1, "device_scale_factor": 1},
                        "mobile": False,
                        "has_touch": False
                    }
                ]
            },
        )
        _write_json(
            result_path,
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("7" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["android.chrome.real.manual"],
                    "lens_count": 2,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                    "visual_status": "passed",
                    "test_evidence_status": "clean"
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": []
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "manual_attestation.result.json",
            {
                "runner_version": "atlas.qa.manual-attestation.validate.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "run_id": "run-1",
                "status": "invalid",
                "attestation_count": 1,
                "attestations": [{"lens_id": "android.chrome.real.manual", "status": "invalid"}],
                "finding_count": 1,
                "findings": [{"severity": "error", "code": "missing_attestation_screenshot", "message": "android missing"}],
            },
        )
        waiver_path = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "waivers" / "android.chrome.real.manual.waiver.json"
        _write_json(
            waiver_path,
            {
                "contract_version": "atlas.qa.waiver.v1",
                "waiver_id": "wrong-run:android.chrome.real.manual:waiver",
                "repo_id": "fitness",
                "scenario_id": "fitness.progression-pr-smoke",
                "run_id": "wrong-run",
                "waived_lane": "android.chrome.real.manual",
                "reason": "Android device/provider unavailable in current operator environment",
                "operator": "atlas-operator",
                "operator_identity": "local:test",
                "created_at": "2026-05-12T00:00:00Z",
                "expires_at": "2099-01-01T00:00:00Z",
                "evidence_present": ["android.chrome.emulated"],
                "limitation": "Android physical proof was not captured"
            },
        )
        promotion = promote_run(root=root, result_path=result_path, artifact_path=artifact_path, scenario_path=scenario_path)
        self.assertEqual("blocked", promotion["promotion_status"])
        self.assertEqual([], promotion["waived_lanes"])
        self.assertTrue(any("run_id does not match" in item for item in promotion["blocking_reasons"]))

    def test_visual_diff_identical_images_pass(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        baseline_dir = root / "data" / "atlas" / "qa" / "baselines" / "fitness.progression-pr-smoke"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = baseline_dir / "desktop.chromium.emulated.png"
        baseline_path.write_bytes(screenshot.read_bytes())
        self._write_baseline_manifest(root=root, baseline_path=baseline_path, lens_id="desktop.chromium.emulated")
        scenario = {
            "visual_assertions": [
                {
                    "lens_id": "desktop.chromium.emulated",
                    "baseline_ref": "data/atlas/qa/baselines/fitness.progression-pr-smoke/desktop.chromium.emulated.png",
                    "max_pixel_delta": 0,
                }
            ]
        }
        manifest = load_json_object(manifest_path)
        receipts, findings = evaluate_visual_diffs(
            root=root,
            run_root=manifest_path.parent,
            scenario_payload=scenario,
            artifact_payload=manifest,
            dry_run=False,
        )
        self.assertEqual("passed", receipts[0]["status"])
        self.assertFalse(any(item["severity"] == "error" for item in findings))

    def test_visual_diff_changed_image_fails(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        baseline_dir = root / "data" / "atlas" / "qa" / "baselines" / "fitness.progression-pr-smoke"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = baseline_dir / "desktop.chromium.emulated.png"
        baseline_path.write_bytes(screenshot.read_bytes())
        self._write_baseline_manifest(root=root, baseline_path=baseline_path, lens_id="desktop.chromium.emulated")
        Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(screenshot, format="PNG")
        manifest = load_json_object(manifest_path)
        digest = sha256_bytes(screenshot.read_bytes())
        manifest["artifacts"][0]["checksum_sha256"] = digest
        manifest["artifacts"][0]["evidence"]["artifact_sha256"] = digest
        _write_json(manifest_path, manifest)
        receipts, findings = evaluate_visual_diffs(
            root=root,
            run_root=manifest_path.parent,
            scenario_payload={
                "visual_assertions": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "baseline_ref": "data/atlas/qa/baselines/fitness.progression-pr-smoke/desktop.chromium.emulated.png",
                        "max_pixel_delta": 0,
                    }
                ]
            },
            artifact_payload=load_json_object(manifest_path),
            dry_run=False,
        )
        self.assertEqual("failed", receipts[0]["status"])
        self.assertTrue(any(item["code"] == "visual_diff_failed" for item in findings))

    def test_visual_diff_ignored_region_prevents_false_failure(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        baseline_dir = root / "data" / "atlas" / "qa" / "baselines" / "fitness.progression-pr-smoke"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = baseline_dir / "desktop.chromium.emulated.png"
        baseline_path.write_bytes(screenshot.read_bytes())
        self._write_baseline_manifest(root=root, baseline_path=baseline_path, lens_id="desktop.chromium.emulated")
        with Image.open(screenshot) as image:
            changed = image.copy()
            changed.putpixel((0, 0), (255, 0, 0, 255))
            changed.save(screenshot, format="PNG")
        manifest = load_json_object(manifest_path)
        digest = sha256_bytes(screenshot.read_bytes())
        manifest["artifacts"][0]["checksum_sha256"] = digest
        manifest["artifacts"][0]["evidence"]["artifact_sha256"] = digest
        _write_json(manifest_path, manifest)
        receipts, findings = evaluate_visual_diffs(
            root=root,
            run_root=manifest_path.parent,
            scenario_payload={
                "visual_assertions": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "baseline_ref": "data/atlas/qa/baselines/fitness.progression-pr-smoke/desktop.chromium.emulated.png",
                        "max_pixel_delta": 0,
                        "ignored_regions": [{"x": 0, "y": 0, "width": 1, "height": 1}],
                    }
                ]
            },
            artifact_payload=load_json_object(manifest_path),
            dry_run=False,
        )
        self.assertEqual("passed", receipts[0]["status"])
        self.assertFalse(any(item["severity"] == "error" for item in findings))

    def test_report_run_creates_html_and_markdown(self) -> None:
        root = self._temp_root()
        artifact_path, _ = self._base_manifest(root=root)
        run_root = artifact_path.parent
        _write_json(
            run_root / "matrix.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("7" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "executed",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["iphone.webkit.real"],
                    "visual_status": "passed",
                    "visual_diff_count": 1,
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0
                },
                "matrix": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "lens_profile_id": "desktop.chromium",
                        "proof_kind": "emulated",
                        "evidence_kind": "emulated_browser",
                        "promotion_tier": "emulated_browser",
                        "fallback_behavior": "blocked",
                        "execution_mode": "browser_capture",
                        "status": "pass"
                    }
                ],
                "findings": [],
                "artifact_manifest_refs": []
            },
        )
        _write_json(
            run_root / "evaluated.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("8" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["iphone.webkit.real"],
                    "visual_status": "passed",
                    "visual_diff_count": 1,
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": [],
                "visual_diffs": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "baseline_ref": "data/atlas/qa/baselines/fitness.progression-pr-smoke/desktop.chromium.emulated.png",
                        "max_pixel_delta": 0,
                        "status": "passed",
                        "evaluated_at": "2026-05-11T00:00:00Z",
                        "changed_pixels": 0
                    }
                ]
            },
        )
        _write_json(
            run_root / "promotion.record.json",
            {
                "contract_version": "atlas.qa.promotion.v1",
                "promotion_id": "sha256:" + ("9" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "evaluator_version": "test",
                "run_id": "run-1",
                "scenario_id": "fitness.progression-pr-smoke",
                "repo_id": "fitness",
                "criticality": "high",
                "promotion_status": "manual_review",
                "highest_satisfied_tier": "emulated_browser",
                "satisfied_evidence_tiers": ["emulated_browser"],
                "missing_evidence_tiers": ["physical_device"],
                "manual_required_lanes": ["iphone.webkit.real"],
                "decision": "manual_review",
                "summary": {
                    "executable_truth": "clean",
                    "artifact_coverage": "complete",
                    "real_device_proof": "manual_required",
                    "visual_status": "passed",
                    "governance_status": "clean",
                    "flake_status": "none"
                },
                "blocking_reasons": [],
                "manual_gaps": ["Real-device certification still requires manual completion."],
                "governance": {"status": "clean", "critical_count": 0, "error_count": 0},
                "source_refs": {"scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json", "result_ref": "runtime/atlas/qa/runs/run-1/evaluated.result.json", "artifact_refs": ["runtime/atlas/qa/runs/run-1/artifacts.manifest.json"]},
                "operator_summary": ["Manual review required before promotion."]
            },
        )
        report = report_run(root=root, run_id="run-1")
        self.assertTrue((root / report["report_html_ref"]).exists())
        self.assertTrue((root / report["report_md_ref"]).exists())
        self.assertTrue((root / report["report_summary_ref"]).exists())
        payload = load_json_object(root / report["report_summary_ref"])
        self.assertEqual("manual_review", payload["promotion_display_status"])

    def test_manual_attestation_scaffold_creates_template(self) -> None:
        root = self._temp_root()
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / "run-1"
        _write_json(
            run_root / "evaluated.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("a" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["iphone.webkit.real"],
                    "visual_status": "not_configured",
                    "visual_diff_count": 0,
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0
                },
                "matrix": [
                    {
                        "lens_id": "iphone.webkit.real",
                        "lens_profile_id": "iphone.webkit",
                        "proof_kind": "real",
                        "evidence_kind": "physical_device",
                        "promotion_tier": "physical_device",
                        "fallback_behavior": "manual_attestation",
                        "execution_mode": "manual_external",
                        "status": "manual_required",
                        "browser_engine": "webkit"
                    }
                ],
                "findings": [],
                "artifact_manifest_refs": []
            },
        )
        report = scaffold_manual_attestations(root=root, run_id="run-1")
        self.assertEqual(1, report["created_count"])
        template_path = root / report["files"][0]["attestation_ref"]
        self.assertTrue(template_path.exists())

    def test_validate_attestations_for_run_writes_report(self) -> None:
        root = self._temp_root()
        screenshot = root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / "iphone.webkit.real" / "manual.png"
        _png(screenshot)
        _manual_attestation(root=root, screenshot=screenshot)
        report = validate_attestations_for_run(root=root, run_id="run-1")
        self.assertEqual("clean", report["status"])
        self.assertTrue((root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "manual_attestation.result.json").exists())

    def test_manual_attestation_packet_prep_renders_markdown(self) -> None:
        root = self._temp_root()
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / "run-1"
        _write_json(
            run_root / "evaluated.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("b" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["iphone.webkit.real"],
                    "visual_status": "not_configured",
                    "visual_diff_count": 0,
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [
                    {
                        "lens_id": "iphone.webkit.real",
                        "lens_profile_id": "iphone.webkit",
                        "proof_kind": "real",
                        "evidence_kind": "physical_device",
                        "promotion_tier": "physical_device",
                        "fallback_behavior": "manual_attestation",
                        "execution_mode": "manual_external",
                        "status": "manual_required",
                        "browser_engine": "webkit",
                    }
                ],
                "findings": [],
                "artifact_manifest_refs": [],
            },
        )
        _write_json(
            run_root / "promotion.record.json",
            {
                "promotion_status": "manual_review",
                "manual_required_lanes": ["iphone.webkit.real"],
            },
        )
        report = build_manual_attestation_packet_prep(root=root, run_id="run-1")
        markdown_path = root / report["output_ref"]
        self.assertTrue(markdown_path.exists())
        body = markdown_path.read_text(encoding="utf-8")
        self.assertIn("run-1", body)
        self.assertIn("iphone.webkit.real", body)
        self.assertIn("captures/iphone.webkit.real/manual.png", body)
        self.assertEqual("manual_review", report["promotion_status"])
        self.assertEqual("invalid", report["validation_status"])
        self.assertEqual(["iphone.webkit.real"], report["open_manual_required_lanes"])
        self.assertEqual([], report["validated_manual_attestation_lanes"])

    def test_manual_attestation_packet_prep_partitions_validated_and_open_lanes(self) -> None:
        root = self._temp_root()
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / "run-1"
        _write_json(
            run_root / "evaluated.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("b" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["desktop.chromium.real", "iphone.webkit.real"],
                    "visual_status": "not_configured",
                    "visual_diff_count": 0,
                    "lens_count": 2,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [
                    {
                        "lens_id": "desktop.chromium.real",
                        "lens_profile_id": "desktop.chromium",
                        "proof_kind": "real",
                        "evidence_kind": "physical_device",
                        "promotion_tier": "physical_device",
                        "fallback_behavior": "manual_attestation",
                        "execution_mode": "manual_external",
                        "status": "manual_required",
                        "browser_engine": "chromium",
                    },
                    {
                        "lens_id": "iphone.webkit.real",
                        "lens_profile_id": "iphone.webkit",
                        "proof_kind": "real",
                        "evidence_kind": "physical_device",
                        "promotion_tier": "physical_device",
                        "fallback_behavior": "manual_attestation",
                        "execution_mode": "manual_external",
                        "status": "manual_required",
                        "browser_engine": "webkit",
                    },
                ],
                "findings": [],
                "artifact_manifest_refs": [],
            },
        )
        _write_json(
            run_root / "promotion.record.json",
            {
                "promotion_status": "manual_review",
                "manual_required_lanes": ["desktop.chromium.real", "iphone.webkit.real"],
            },
        )
        _write_json(
            run_root / "manual-attestation.scaffold.json",
            {
                "runner_version": "atlas.qa.manual-attestation.scaffold.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "run_id": "run-1",
                "created_count": 0,
                "manual_required_lanes": ["desktop.chromium.real", "iphone.webkit.real"],
                "files": [
                    {
                        "lens_id": "desktop.chromium.real",
                        "attestation_ref": "runtime/atlas/qa/runs/run-1/manual-attestations/desktop.chromium.real.manual.json",
                        "expected_screenshot_ref": "runtime/atlas/qa/runs/run-1/captures/desktop.chromium.real/manual.png",
                        "status": "existing",
                    },
                    {
                        "lens_id": "iphone.webkit.real",
                        "attestation_ref": "runtime/atlas/qa/runs/run-1/manual-attestations/iphone.webkit.real.manual.json",
                        "expected_screenshot_ref": "runtime/atlas/qa/runs/run-1/captures/iphone.webkit.real/manual.png",
                        "status": "existing",
                    },
                ],
            },
        )
        _write_json(
            run_root / "manual_attestation.result.json",
            {
                "runner_version": "atlas.qa.manual-attestation.validate.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "run_id": "run-1",
                "status": "invalid",
                "attestation_count": 2,
                "attestations": [
                    {"lens_id": "desktop.chromium.real", "status": "valid"},
                    {"lens_id": "iphone.webkit.real", "status": "invalid"},
                ],
                "finding_count": 1,
                "findings": [
                    {
                        "severity": "error",
                        "code": "missing_attestation_screenshot",
                        "message": "iphone missing",
                    }
                ],
            },
        )

        report = build_manual_attestation_packet_prep(root=root, run_id="run-1")
        self.assertEqual(["desktop.chromium.real"], report["validated_manual_attestation_lanes"])
        self.assertEqual(["iphone.webkit.real"], report["open_manual_required_lanes"])
        body = (root / report["output_ref"]).read_text(encoding="utf-8")
        self.assertIn("Still-open manual lanes: `iphone.webkit.real`", body)
        self.assertIn("Validated manual lanes: `desktop.chromium.real`", body)

    def test_report_run_marks_valid_manual_attestation_in_per_lens(self) -> None:
        root = self._temp_root()
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / "run-1"
        screenshot = run_root / "captures" / "desktop.chromium.real" / "manual.png"
        _png(screenshot)
        _write_json(
            run_root / "matrix.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "executed",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["desktop.chromium.real", "iphone.webkit.real"],
                    "visual_status": "passed",
                    "visual_diff_count": 0,
                    "lens_count": 2,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [
                    {
                        "lens_id": "desktop.chromium.real",
                        "proof_kind": "real",
                        "evidence_kind": "physical_device",
                        "status": "manual_required",
                    },
                    {
                        "lens_id": "iphone.webkit.real",
                        "proof_kind": "real",
                        "evidence_kind": "physical_device",
                        "status": "manual_required",
                    },
                ],
                "findings": [],
                "artifact_manifest_refs": [],
            },
        )
        _write_json(
            run_root / "evaluated.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["desktop.chromium.real", "iphone.webkit.real"],
                    "visual_status": "passed",
                    "visual_diff_count": 0,
                    "lens_count": 2,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": [],
                "visual_diffs": [],
            },
        )
        _write_json(
            run_root / "artifacts.manifest.json",
            {
                "contract_version": "atlas.qa.artifact.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "run_id": "run-1",
                "scenario_id": "fitness.progression-pr-smoke",
                "adapter_id": "fitness.web",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "stage": "collected",
                "mode": "execute",
                "evidence_grade": "evidence",
                "git_sha": "abcdef1234567890",
                "environment": {"execution_root": "runtime/atlas/qa/runs/run-1", "target_url": "http://127.0.0.1:3002"},
                "lenses": {},
                "attestations": [],
                "artifacts": [],
                "summary": {
                    "artifact_count": 0,
                    "required_count": 0,
                    "present_count": 0,
                    "missing_count": 0,
                    "manual_required_count": 0,
                    "manual_attested_count": 0,
                    "invalid_count": 0,
                },
            },
        )
        _write_json(
            run_root / "promotion.record.json",
            {
                "contract_version": "atlas.qa.promotion.v1",
                "promotion_id": "sha256:" + ("9" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "evaluator_version": "test",
                "run_id": "run-1",
                "scenario_id": "fitness.progression-pr-smoke",
                "repo_id": "fitness",
                "criticality": "high",
                "promotion_status": "manual_review",
                "evidence_profile": "web_visual",
                "highest_satisfied_tier": "emulated_browser",
                "missing_evidence_tiers": ["physical_device"],
                "manual_required_lanes": ["iphone.webkit.real"],
                "waived_lanes": [],
                "waiver_refs": [],
                "waiver_reasons": [],
                "decision": "manual_review",
                "summary": {
                    "executable_truth": "clean",
                    "artifact_coverage": "complete",
                    "real_device_proof": "manual_required",
                    "visual_status": "passed",
                    "test_evidence_status": "clean",
                    "evidence_profile": "web_visual",
                    "governance_status": "clean",
                    "flake_status": "none",
                },
                "blocking_reasons": [],
                "manual_gaps": ["Real-device certification still requires manual completion."],
                "governance": {"status": "clean", "critical_count": 0, "error_count": 0},
                "source_refs": {
                    "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                    "result_ref": "runtime/atlas/qa/runs/run-1/evaluated.result.json",
                    "artifact_refs": ["runtime/atlas/qa/runs/run-1/artifacts.manifest.json"],
                },
                "operator_summary": ["Manual review required before promotion."],
            },
        )
        _write_json(
            run_root / "manual-attestations" / "desktop.chromium.real.manual.json",
            {
                "contract_version": "atlas.qa.manual_attestation.v1",
                "attestation_id": "att-1",
                "operator": "atlas-operator",
                "operator_identity": "local:test",
                "scenario_id": "fitness.progression-pr-smoke",
                "adapter_id": "fitness.web",
                "run_id": "run-1",
                "lens_id": "desktop.chromium.real",
                "device_model": "Desktop Browser",
                "os_name": "Windows",
                "os_version": "11",
                "browser_name": "chromium",
                "browser_version": "1.0",
                "capture_timestamp": "2026-05-11T00:00:00Z",
                "expires_at": "2099-01-01T00:00:00Z",
                "screenshot_artifacts": [
                    {
                        "path_ref": "runtime/atlas/qa/runs/run-1/captures/desktop.chromium.real/manual.png",
                        "checksum_sha256": "sha256:" + sha256_bytes(screenshot.read_bytes()),
                    }
                ],
                "supporting_artifacts": [],
                "notes": [],
            },
        )
        _write_json(
            run_root / "manual_attestation.result.json",
            {
                "runner_version": "atlas.qa.manual-attestation.validate.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "run_id": "run-1",
                "status": "invalid",
                "attestation_count": 2,
                "attestations": [
                    {
                        "attestation_id": "att-1",
                        "attestation_ref": "runtime/atlas/qa/runs/run-1/manual-attestations/desktop.chromium.real.manual.json",
                        "run_id": "run-1",
                        "scenario_id": "fitness.progression-pr-smoke",
                        "adapter_id": "fitness.web",
                        "lens_id": "desktop.chromium.real",
                        "operator": "atlas-operator",
                        "capture_method": "manual_attestation",
                        "status": "valid",
                    },
                    {
                        "attestation_id": "att-2",
                        "attestation_ref": "runtime/atlas/qa/runs/run-1/manual-attestations/iphone.webkit.real.manual.json",
                        "run_id": "run-1",
                        "scenario_id": "fitness.progression-pr-smoke",
                        "adapter_id": "fitness.web",
                        "lens_id": "iphone.webkit.real",
                        "operator": "atlas-operator",
                        "capture_method": "manual_attestation",
                        "status": "invalid",
                    },
                ],
                "finding_count": 1,
                "findings": [{"severity": "error", "code": "missing_attestation_screenshot", "message": "iphone missing"}],
            },
        )
        report = report_run(root=root, run_id="run-1")
        payload = load_json_object(root / report["report_summary_ref"])
        desktop = next(item for item in payload["per_lens"] if item["lens_id"] == "desktop.chromium.real")
        iphone = next(item for item in payload["per_lens"] if item["lens_id"] == "iphone.webkit.real")
        self.assertEqual("manual_attested", desktop["status"])
        self.assertEqual("runtime/atlas/qa/runs/run-1/captures/desktop.chromium.real/manual.png", desktop["screenshot_ref"])
        self.assertEqual("manual_required", iphone["status"])

    def test_adapter_prepare_command_is_accepted(self) -> None:
        adapter = {
            "contract_version": "atlas.qa.adapter.v1",
            "adapter_id": "fixture.web",
            "repo_id": "fitness",
            "repo_path": "repos/fawxzzy-fitness",
            "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
            "prepare": {"kind": "command", "command": "npm ci"},
            "commands": {"verify": {"command": "npm run verify"}},
            "lenses": [
                {
                    "lens_id": "desktop.chromium.emulated",
                    "profile_id": "desktop.chromium",
                    "proof_kind": "emulated",
                    "execution_mode": "repo_command",
                    "command_ref": "verify",
                }
            ],
        }
        errors = validate_adapter_manifest(adapter, root=ROOT)
        self.assertFalse(any(item.startswith("prepare") for item in errors), errors)

    def test_adapter_prepare_requires_command(self) -> None:
        adapter = {
            "contract_version": "atlas.qa.adapter.v1",
            "adapter_id": "fixture.web",
            "repo_id": "fitness",
            "repo_path": "repos/fawxzzy-fitness",
            "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
            "prepare": {"kind": "command", "command": ""},
            "commands": {"verify": {"command": "npm run verify"}},
            "lenses": [
                {
                    "lens_id": "desktop.chromium.emulated",
                    "profile_id": "desktop.chromium",
                    "proof_kind": "emulated",
                    "execution_mode": "repo_command",
                    "command_ref": "verify",
                }
            ],
        }
        errors = validate_adapter_manifest(adapter, root=ROOT)
        self.assertTrue(any(item == "prepare.command must be a non-empty string when prepare is present." for item in errors), errors)

    def test_adapter_manifest_can_skip_repo_path_existence_for_root_only_ci(self) -> None:
        adapter = load_json_object(ROOT / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json")
        errors = validate_adapter_manifest(adapter, root=self._temp_root(), require_repo_path_exists=False)
        self.assertFalse(any(item.startswith("repo_path does not exist:") for item in errors), errors)

    def test_scenario_manifest_can_skip_repo_path_existence_for_root_only_ci(self) -> None:
        scenario = load_json_object(ROOT / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json")
        errors = validate_scenario_manifest(scenario, root=self._temp_root(), require_repo_path_exists=False)
        self.assertFalse(any(item.startswith("repo_path does not exist:") for item in errors), errors)

    def test_provider_manifest_validates(self) -> None:
        payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "providers" / "mock.physical-device.v1.json")
        self.assertEqual([], validate_provider_manifest(payload))

    def test_browserstack_provider_missing_env_fails_clearly(self) -> None:
        payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "providers" / "browserstack.playwright.v1.json")
        with mock.patch.dict("os.environ", {"BROWSERSTACK_USERNAME": "", "BROWSERSTACK_ACCESS_KEY": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "BrowserStack provider is missing required environment variables"):
                capture_with_provider(
                    root=ROOT,
                    provider_manifest_ref="ops/atlas/qa/providers/browserstack.playwright.v1.json",
                    config={
                        "repoRoot": str(ROOT / "repos" / "fawxzzy-fitness"),
                        "outputDir": str(ROOT / "tmp" / "qa-provider-test"),
                        "browserEngine": "chromium",
                        "viewport": {"width": 1440, "height": 1024, "device_scale_factor": 1},
                        "sourceUrl": "https://example.com",
                        "runId": "run-1",
                        "scenarioId": "fixture",
                        "adapterId": "fixture.web",
                        "repoId": "fitness",
                        "gitSha": "abcdef1234567890",
                        "lensId": "desktop.chromium.real",
                        "lensProfileId": "desktop.chromium",
                        "deviceModel": "Windows Desktop",
                        "osName": "Windows",
                        "osVersion": "11",
                        "browserName": "chrome",
                        "browserVersion": "latest"
                    },
                )
        self.assertEqual([], validate_provider_manifest(payload))

    def test_provider_status_reports_browserstack_unavailable_without_credentials(self) -> None:
        with mock.patch.dict("os.environ", {"BROWSERSTACK_USERNAME": "", "BROWSERSTACK_ACCESS_KEY": ""}, clear=False):
            status = _provider_status(root=ROOT, provider="browserstack.playwright.v1")
        self.assertEqual("provider_unavailable", status["status"])
        self.assertEqual(
            ["BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY"],
            status["missing_env_vars"],
        )

    def test_wait_for_url_reports_adapter_server_log_tail_when_process_exits_early(self) -> None:
        root = self._temp_root()
        log_path = root / "runtime" / "atlas" / "qa" / "adapter-server" / "fitness.latest.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("fitness dev server crashed\nError: missing fixture\n", encoding="utf-8")
        process = mock.Mock()
        process.poll.return_value = 17
        process.returncode = 17
        with self.assertRaisesRegex(RuntimeError, "adapter server log tail"):
            _wait_for_url("http://127.0.0.1:3002/api/health", timeout_s=1, process=process, log_path=log_path)

    def test_provider_readiness_reports_browserstack_ready_for_fitness_release_lenses(self) -> None:
        with mock.patch.dict("os.environ", {"BROWSERSTACK_USERNAME": "user", "BROWSERSTACK_ACCESS_KEY": "key"}, clear=False):
            report = provider_readiness(
                root=ROOT,
                provider_manifest_ref="ops/atlas/qa/providers/browserstack.playwright.v1.json",
                adapter_id="fitness.web",
                scenario_id="fitness.progression-pr-smoke",
            )
        self.assertEqual(
            ["desktop.chromium.real", "android.chrome.real", "iphone.webkit.real"],
            report["requested_physical_lenses"],
        )
        self.assertEqual([], report["unsupported_requested_lenses"])
        self.assertTrue(report["live_smoke_eligible"])

    def test_github_secret_readiness_reports_missing_required_secrets(self) -> None:
        root = self._temp_root()
        report = github_secret_readiness(
            root=root,
            repo="fawxzzy/ATLAS",
            required_secret_names=["BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY"],
            token="test-token",
            secret_names_fetcher=lambda repo, token: [],
        )
        self.assertEqual("blocked", report["status"])
        self.assertEqual(
            ["BROWSERSTACK_ACCESS_KEY", "BROWSERSTACK_USERNAME"],
            report["missing_required_secret_names"],
        )
        latest = load_json_object(root / "runtime" / "atlas" / "qa" / "github-secret-readiness.latest.json")
        self.assertEqual(0, latest["available_secret_count"])
        self.assertEqual("missing", latest["required_secret_statuses"]["BROWSERSTACK_USERNAME"])
        self.assertEqual("missing", latest["required_secret_statuses"]["BROWSERSTACK_ACCESS_KEY"])

    def test_github_secret_readiness_reports_present_required_secrets(self) -> None:
        root = self._temp_root()
        report = github_secret_readiness(
            root=root,
            repo="fawxzzy/ATLAS",
            required_secret_names=["BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY"],
            token="test-token",
            secret_names_fetcher=lambda repo, token: [
                "BROWSERSTACK_ACCESS_KEY",
                "BROWSERSTACK_USERNAME",
                "UNRELATED_SECRET",
            ],
        )
        self.assertEqual("ready", report["status"])
        self.assertEqual([], report["missing_required_secret_names"])
        latest = load_json_object(root / "runtime" / "atlas" / "qa" / "github-secret-readiness.latest.json")
        self.assertEqual("ready", latest["status"])
        self.assertEqual(3, latest["available_secret_count"])
        self.assertEqual(
            ["BROWSERSTACK_ACCESS_KEY", "BROWSERSTACK_USERNAME"],
            latest["browserstack_named_secret_names"],
        )

    def test_release_gate_packet_renders_combined_operator_packet(self) -> None:
        root = self._temp_root()
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / "run-1"
        provider_src = ROOT / "ops" / "atlas" / "qa" / "providers" / "browserstack.playwright.v1.json"
        adapter_src = ROOT / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json"
        scenario_src = ROOT / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json"
        provider_schema_src = ROOT / "schemas" / "atlas.qa.provider.v1.json"
        provider_dst = root / "ops" / "atlas" / "qa" / "providers" / "browserstack.playwright.v1.json"
        adapter_dst = root / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json"
        scenario_dst = root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json"
        provider_schema_dst = root / "schemas" / "atlas.qa.provider.v1.json"
        provider_dst.parent.mkdir(parents=True, exist_ok=True)
        adapter_dst.parent.mkdir(parents=True, exist_ok=True)
        scenario_dst.parent.mkdir(parents=True, exist_ok=True)
        provider_schema_dst.parent.mkdir(parents=True, exist_ok=True)
        provider_dst.write_text(provider_src.read_text(encoding="utf-8"), encoding="utf-8")
        adapter_dst.write_text(adapter_src.read_text(encoding="utf-8"), encoding="utf-8")
        scenario_dst.write_text(scenario_src.read_text(encoding="utf-8"), encoding="utf-8")
        provider_schema_dst.write_text(provider_schema_src.read_text(encoding="utf-8"), encoding="utf-8")
        _write_json(
            run_root / "evaluated.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("c" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "manual_required",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": ["physical_device"],
                    "manual_required_lanes": ["android.chrome.real", "iphone.webkit.real"],
                    "visual_status": "not_configured",
                    "visual_diff_count": 0,
                    "lens_count": 2,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [
                    {
                        "lens_id": "android.chrome.real",
                        "status": "manual_required",
                        "browser_engine": "chromium",
                    },
                    {
                        "lens_id": "iphone.webkit.real",
                        "status": "manual_required",
                        "browser_engine": "webkit",
                    },
                ],
                "findings": [],
                "artifact_manifest_refs": [],
            },
        )
        _write_json(
            run_root / "promotion.record.json",
            {
                "promotion_status": "manual_review",
                "manual_required_lanes": ["android.chrome.real", "iphone.webkit.real"],
            },
        )
        _write_json(
            run_root / "manual_attestation.result.json",
            {
                "runner_version": "atlas.qa.manual-attestation.validate.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "run_id": "run-1",
                "status": "invalid",
                "attestation_count": 2,
                "attestations": [
                    {"lens_id": "android.chrome.real", "status": "invalid"},
                    {"lens_id": "iphone.webkit.real", "status": "valid"},
                ],
                "finding_count": 1,
                "findings": [
                    {"severity": "error", "code": "missing_attestation_screenshot", "message": "android missing"}
                ],
            },
        )
        report = build_release_gate_packet(
            root=root,
            run_id="run-1",
            repo="fawxzzy/ATLAS",
            provider_manifest_ref="ops/atlas/qa/providers/browserstack.playwright.v1.json",
            adapter_id="fitness.web",
            scenario_id="fitness.progression-pr-smoke",
            required_secret_names=["BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY"],
            token="test-token",
            secret_names_fetcher=lambda repo, token: [],
        )
        packet_path = root / report["output_ref"]
        self.assertTrue(packet_path.exists())
        body = packet_path.read_text(encoding="utf-8")
        self.assertIn("manual_review", body)
        self.assertIn("BROWSERSTACK_USERNAME", body)
        self.assertIn("android.chrome.real", body)
        self.assertIn("Manual-required lanes still open: `android.chrome.real`", body)
        self.assertIn("Validated manual lanes: `iphone.webkit.real`", body)
        self.assertEqual("blocked", report["github_secret_status"])
        self.assertEqual(["android.chrome.real"], report["open_manual_required_lanes"])
        self.assertEqual(["iphone.webkit.real"], report["validated_manual_attestation_lanes"])

    def test_provider_override_only_mutates_supported_real_lenses(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa" / "providers").mkdir(parents=True, exist_ok=True)
        provider_path = root / "ops" / "atlas" / "qa" / "providers" / "limited.provider.json"
        _write_json(
            provider_path,
            {
                "contract_version": "atlas.qa.provider.v1",
                "provider_id": "mock.physical-device",
                "provider_type": "mock",
                "auth_env_vars": [],
                "supported_lenses": ["desktop.chromium.real"],
                "artifact_capabilities": ["screenshot", "console_log", "network_log"],
            },
        )
        adapter_path = root / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json"
        adapter_path.parent.mkdir(parents=True, exist_ok=True)
        adapter_payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json")
        _write_json(adapter_path, adapter_payload)
        override_path, handle = _provider_override_file(
            root=root,
            adapter_payload=adapter_payload,
            adapter_path=adapter_path,
            provider="limited.provider",
        )
        self.addCleanup(lambda: handle.cleanup() if handle is not None else None)
        self.assertIsNotNone(override_path)
        overridden = load_json_object(override_path)
        by_lens = {item["lens_id"]: item for item in overridden["lenses"]}
        self.assertEqual("provider_capture", by_lens["desktop.chromium.real"]["execution_mode"])
        self.assertEqual("manual_external", by_lens["android.chrome.real"]["execution_mode"])
        self.assertEqual("manual_external", by_lens["iphone.webkit.real"]["execution_mode"])

    def test_browserstack_capture_builds_ios_capabilities_without_desktop_flags(self) -> None:
        script = """
import { buildCapabilities } from './ops/atlas/qa/capture_browserstack.mjs';
const caps = buildCapabilities({}, {
  runId: 'run-1',
  scenarioId: 'fitness.progression-pr-smoke',
  lensId: 'iphone.webkit.real',
  browserEngine: 'webkit',
  viewport: { width: 393, height: 852 },
  deviceModel: 'iPhone 15',
  osName: 'iOS',
  osVersion: '17',
  browserName: 'safari',
  browserVersion: '17'
});
console.log(JSON.stringify(caps));
"""
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        caps = json.loads(completed.stdout)
        self.assertEqual("safari", caps["browser"])
        self.assertEqual("iPhone 15", caps["deviceName"])
        self.assertEqual("17", caps["osVersion"])
        self.assertEqual("true", caps["realMobile"])
        self.assertNotIn("resolution", caps)
        self.assertNotIn("browserstack.console", caps)

    def test_browserstack_capture_builds_android_capabilities_for_real_mobile(self) -> None:
        script = """
import { buildCapabilities } from './ops/atlas/qa/capture_browserstack.mjs';
const caps = buildCapabilities({}, {
  runId: 'run-1',
  scenarioId: 'fitness.progression-pr-smoke',
  lensId: 'android.chrome.real',
  browserEngine: 'chromium',
  viewport: { width: 412, height: 915 },
  deviceModel: 'Samsung Galaxy S23',
  osName: 'Android',
  osVersion: '13.0',
  browserName: 'chrome',
  browserVersion: 'latest'
});
console.log(JSON.stringify(caps));
"""
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        caps = json.loads(completed.stdout)
        self.assertEqual("chrome", caps["browser"])
        self.assertEqual("Samsung Galaxy S23", caps["deviceName"])
        self.assertEqual("13.0", caps["osVersion"])
        self.assertEqual("true", caps["realMobile"])
        self.assertNotIn("resolution", caps)

    def test_browserstack_capture_builds_desktop_capabilities_without_provider_resolution(self) -> None:
        script = """
import { buildCapabilities } from './ops/atlas/qa/capture_browserstack.mjs';
const caps = buildCapabilities({}, {
  runId: 'run-1',
  scenarioId: 'fitness.progression-pr-smoke',
  lensId: 'desktop.chromium.real',
  browserEngine: 'chromium',
  viewport: { width: 1440, height: 1024 },
  deviceModel: 'Windows Desktop',
  osName: 'Windows',
  osVersion: '11',
  browserName: 'chrome',
  browserVersion: 'latest'
});
console.log(JSON.stringify(caps));
"""
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        caps = json.loads(completed.stdout)
        self.assertEqual("chrome", caps["browser"])
        self.assertEqual("Windows", caps["os"])
        self.assertEqual("11", caps["os_version"])
        self.assertEqual("latest", caps["browser_version"])
        self.assertNotIn("resolution", caps)

    def test_browserstack_capture_enables_local_testing_for_loopback_targets(self) -> None:
        script = """
import { buildCapabilities } from './ops/atlas/qa/capture_browserstack.mjs';
const caps = buildCapabilities({}, {
  runId: 'run-1',
  scenarioId: 'fitness.progression-pr-smoke',
  lensId: 'desktop.chromium.real',
  browserEngine: 'chromium',
  sourceUrl: 'http://127.0.0.1:3002/dev/mobile-regression',
  viewport: { width: 1440, height: 1024 },
  deviceModel: 'Windows Desktop',
  osName: 'Windows',
  osVersion: '11',
  browserName: 'chrome',
  browserVersion: 'latest'
}, {
  BROWSERSTACK_USERNAME: 'user',
  BROWSERSTACK_ACCESS_KEY: 'key',
  BROWSERSTACK_LOCAL_IDENTIFIER: 'atlas-local-1'
});
console.log(JSON.stringify(caps));
"""
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        caps = json.loads(completed.stdout)
        self.assertEqual("true", caps["browserstack.local"])
        self.assertEqual("atlas-local-1", caps["browserstack.localIdentifier"])

    def test_browserstack_capture_rewrites_loopback_navigation_for_desktop_local(self) -> None:
        script = """
import { resolveBrowserStackNavigationUrl, resolveBrowserStackWaitUntil } from './ops/atlas/qa/capture_browserstack.mjs';
const desktopUrl = resolveBrowserStackNavigationUrl({
  lensId: 'desktop.chromium.real',
  osName: 'Windows',
  sourceUrl: 'http://127.0.0.1:3002/dev/mobile-regression?scenario=today-progression-status'
}, {
  BROWSERSTACK_USERNAME: 'user',
  BROWSERSTACK_ACCESS_KEY: 'key',
  BROWSERSTACK_LOCAL_IDENTIFIER: 'atlas-local-1'
});
const androidUrl = resolveBrowserStackNavigationUrl({
  lensId: 'android.chrome.real',
  osName: 'Android',
  sourceUrl: 'http://127.0.0.1:3002/dev/mobile-regression?scenario=today-progression-status'
}, {
  BROWSERSTACK_USERNAME: 'user',
  BROWSERSTACK_ACCESS_KEY: 'key',
  BROWSERSTACK_LOCAL_IDENTIFIER: 'atlas-local-1'
});
const waitUntilWithSelector = resolveBrowserStackWaitUntil({
  waitUntil: 'networkidle',
  readySelector: "body[data-mobile-regression='true']"
});
const waitUntilWithoutSelector = resolveBrowserStackWaitUntil({
  waitUntil: 'networkidle'
});
console.log(JSON.stringify({ desktopUrl, androidUrl, waitUntilWithSelector, waitUntilWithoutSelector }));
"""
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        urls = json.loads(completed.stdout)
        self.assertEqual(
            "http://bs-local.com:3002/dev/mobile-regression?scenario=today-progression-status",
            urls["desktopUrl"],
        )
        self.assertEqual(
            "http://127.0.0.1:3002/dev/mobile-regression?scenario=today-progression-status",
            urls["androidUrl"],
        )
        self.assertEqual("domcontentloaded", urls["waitUntilWithSelector"])
        self.assertEqual("networkidle", urls["waitUntilWithoutSelector"])

    def test_capture_cache_uses_provider_safe_defaults_for_browserstack_real_lenses(self) -> None:
        adapter_payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json")
        for item in adapter_payload["lenses"]:
            if isinstance(item, dict) and item.get("proof_kind") == "real":
                item["execution_mode"] = "provider_capture"
                item["provider_manifest_ref"] = "ops/atlas/qa/providers/browserstack.playwright.v1.json"

        lens_payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json")
        lens_profiles = {
            str(item["lens_id"]): item
            for item in lens_payload["lenses"]
            if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
        }
        result_payload = {
            "run_id": "run-1",
            "scenario_id": "fitness.progression-pr-smoke",
            "adapter_id": "fitness.web",
            "repo_id": "fitness",
            "git_sha": "abcdef1234567890",
        }
        scenario_payload = {"scenario_id": "fitness.progression-pr-smoke", "entrypoint": {"path": "/dev/mobile-regression"}}
        result_by_lens = {
            "desktop.chromium.real": {"execution_mode": "provider_capture"},
            "android.chrome.real": {"execution_mode": "provider_capture"},
            "iphone.webkit.real": {"execution_mode": "provider_capture"},
        }
        captured: dict[str, dict] = {}

        def _fake_capture_with_provider(*, root: Path, provider_manifest_ref: str, config: dict[str, object]) -> dict[str, object]:
            captured[str(config["lensId"])] = dict(config)
            return {"metadata_path": str(root / "tmp" / f"{config['lensId']}.metadata.json"), "outputs": {}}

        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.dict("os.environ", {"ATLAS_QA_PROVIDER_BASE_URL": "https://atlas-provider.example"}, clear=False):
                with mock.patch("ops.atlas.qa.collect_artifacts.capture_with_provider", side_effect=_fake_capture_with_provider):
                    _capture_cache(
                        execute=True,
                        repo_root=ROOT / "repos" / "fawxzzy-fitness",
                        run_root=Path(temp_dir),
                        adapter=adapter_payload,
                        scenario=scenario_payload,
                        result_payload=result_payload,
                        lens_payload=lens_payload,
                        lens_profiles=lens_profiles,
                        result_by_lens=result_by_lens,
                    )

        self.assertEqual("Windows Desktop", captured["desktop.chromium.real"]["deviceModel"])
        self.assertEqual("Windows", captured["desktop.chromium.real"]["osName"])
        self.assertEqual("11", captured["desktop.chromium.real"]["osVersion"])
        self.assertEqual("chrome", captured["desktop.chromium.real"]["browserName"])
        self.assertEqual("latest", captured["desktop.chromium.real"]["browserVersion"])
        self.assertEqual("attached", captured["desktop.chromium.real"]["readyState"])
        self.assertEqual("https://atlas-provider.example/dev/mobile-regression", captured["desktop.chromium.real"]["sourceUrl"])
        self.assertEqual("Samsung Galaxy S23", captured["android.chrome.real"]["deviceModel"])
        self.assertEqual("Android", captured["android.chrome.real"]["osName"])
        self.assertEqual("13.0", captured["android.chrome.real"]["osVersion"])
        self.assertEqual("iPhone 15", captured["iphone.webkit.real"]["deviceModel"])
        self.assertEqual("iOS", captured["iphone.webkit.real"]["osName"])
        self.assertEqual("17", captured["iphone.webkit.real"]["osVersion"])

    def test_capture_cache_degrades_real_provider_failures_to_manual_required_when_allowed(self) -> None:
        adapter_payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json")
        for item in adapter_payload["lenses"]:
            if isinstance(item, dict) and item.get("proof_kind") == "real":
                item["execution_mode"] = "provider_capture"
                item["provider_manifest_ref"] = "ops/atlas/qa/providers/browserstack.playwright.v1.json"

        lens_payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json")
        lens_profiles = {
            str(item["lens_id"]): item
            for item in lens_payload["lenses"]
            if isinstance(item, dict) and isinstance(item.get("lens_id"), str)
        }
        result_payload = {
            "run_id": "run-1",
            "scenario_id": "fitness.progression-pr-smoke",
            "adapter_id": "fitness.web",
            "repo_id": "fitness",
            "git_sha": "abcdef1234567890",
        }
        scenario_payload = {"scenario_id": "fitness.progression-pr-smoke", "entrypoint": {"path": "/dev/mobile-regression"}}
        result_by_lens = {
            "desktop.chromium.real": {"execution_mode": "provider_capture", "proof_kind": "real", "fallback_behavior": "manual_attestation"},
            "android.chrome.real": {"execution_mode": "provider_capture", "proof_kind": "real", "fallback_behavior": "manual_attestation"},
            "iphone.webkit.real": {"execution_mode": "provider_capture", "proof_kind": "real", "fallback_behavior": "manual_attestation"},
        }
        captured: dict[str, dict] = {}

        def _fake_capture_with_provider(*, root: Path, provider_manifest_ref: str, config: dict[str, object]) -> dict[str, object]:
            lens_id = str(config["lensId"])
            if lens_id == "iphone.webkit.real":
                raise RuntimeError("provider screenshot stalled")
            captured[lens_id] = config
            return {
                "metadata_path": str(root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / lens_id / "capture.metadata.json"),
                "outputs": {
                    "screenshot": str(root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / lens_id / "screenshot.png"),
                    "console_log": str(root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / lens_id / "console.log"),
                    "network_log": str(root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "captures" / lens_id / "network.json"),
                },
            }

        run_root = ROOT / "tmp" / "unit-capture-cache-provider-failure"
        if run_root.exists():
            shutil.rmtree(run_root)
        self.addCleanup(lambda: shutil.rmtree(run_root, ignore_errors=True))

        with mock.patch("ops.atlas.qa.collect_artifacts.capture_with_provider", side_effect=_fake_capture_with_provider):
            cache = _capture_cache(
                execute=True,
                repo_root=ROOT / "repos" / "fawxzzy-fitness",
                run_root=run_root,
                adapter=adapter_payload,
                scenario=scenario_payload,
                result_payload=result_payload,
                lens_payload=lens_payload,
                lens_profiles=lens_profiles,
                result_by_lens=result_by_lens,
            )

        self.assertIn("desktop.chromium.real", cache)
        self.assertIn("android.chrome.real", cache)
        self.assertNotIn("iphone.webkit.real", cache)
        failure_note = run_root / "captures" / "iphone.webkit.real" / "capture.failure.txt"
        self.assertTrue(failure_note.exists())
        self.assertIn("provider screenshot stalled", failure_note.read_text(encoding="utf-8"))

    def test_run_matrix_dry_run_honors_explicit_real_lens_command_ref(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        adapter_dir = Path(temp_dir.name)
        adapter_payload = load_json_object(ROOT / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json")
        for item in adapter_payload["lenses"]:
            if isinstance(item, dict) and item.get("proof_kind") == "real":
                item["execution_mode"] = "provider_capture"
                item["provider_manifest_ref"] = "ops/atlas/qa/providers/browserstack.playwright.v1.json"
                item["command_ref"] = "qa_visual"
        _write_json(adapter_dir / "fitness.web.json", adapter_payload)
        with mock.patch.dict("os.environ", {"ATLAS_QA_PROVIDER_BASE_URL": "https://atlas-provider.example"}, clear=False):
            result = run_matrix(
                root=ROOT,
                scenario_path=ROOT / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json",
                adapter_id="fitness.web",
                adapter_dir=adapter_dir,
                output_root=adapter_dir,
                dry_run=True,
            )
        self.assertFalse(any(item["code"] == "missing_command_ref" for item in result["findings"]))
        real_lenses = [item for item in result["matrix"] if item["proof_kind"] == "real"]
        self.assertTrue(real_lenses)
        self.assertTrue(all(item.get("command_ref") == "qa_visual" for item in real_lenses))
        self.assertTrue(all(item.get("url_target") == "https://atlas-provider.example" for item in real_lenses))

    def test_browserstack_provider_redacts_credentials_from_subprocess_failure(self) -> None:
        username = "atlas-browserstack-user"
        access_key = "atlas-browserstack-key+/="
        encoded_access_key = urllib.parse.quote(access_key, safe="")
        failure = subprocess.CompletedProcess(
            args=["node", "capture_browserstack.mjs"],
            returncode=1,
            stdout="",
            stderr=(
                "BrowserStack connect failed for "
                f'{{"browserstack.username":"{username}","browserstack.accessKey":"{access_key}"}} '
                f"wss://cdp.browserstack.com/playwright?caps=%7B%22browserstack.accessKey%22%3A%22{encoded_access_key}%22%7D "
                f"BROWSERSTACK_ACCESS_KEY={access_key}"
            ),
        )
        with mock.patch.dict(
            "os.environ",
            {"BROWSERSTACK_USERNAME": username, "BROWSERSTACK_ACCESS_KEY": access_key},
            clear=False,
        ):
            with mock.patch("ops.atlas.qa.providers.browserstack_provider.subprocess.run", return_value=failure):
                with self.assertRaises(RuntimeError) as context:
                    capture_with_provider(
                        root=ROOT,
                        provider_manifest_ref="ops/atlas/qa/providers/browserstack.playwright.v1.json",
                        config={
                            "repoRoot": str(ROOT / "repos" / "fawxzzy-fitness"),
                            "outputDir": str(ROOT / "tmp" / "qa-provider-test"),
                            "browserEngine": "chromium",
                            "viewport": {"width": 1440, "height": 1024, "device_scale_factor": 1},
                            "sourceUrl": "https://example.com",
                            "runId": "run-1",
                            "scenarioId": "fixture",
                            "adapterId": "fixture.web",
                            "repoId": "fitness",
                            "gitSha": "abcdef1234567890",
                            "lensId": "desktop.chromium.real",
                            "lensProfileId": "desktop.chromium",
                            "deviceModel": "Windows Desktop",
                            "osName": "Windows",
                            "osVersion": "11",
                            "browserName": "chrome",
                            "browserVersion": "latest",
                        },
                    )
        message = str(context.exception)
        self.assertNotIn(username, message)
        self.assertNotIn(access_key, message)
        self.assertNotIn(encoded_access_key, message)
        self.assertIn("[REDACTED]", message)

    def test_browserstack_provider_retries_transient_socket_idle_failure(self) -> None:
        failure = subprocess.CompletedProcess(
            args=["node", "capture_browserstack.mjs"],
            returncode=1,
            stdout="",
            stderr="Provider screenshot failed for lens iphone.webkit.real. reason=Socket idle from a long time",
        )
        success = subprocess.CompletedProcess(
            args=["node", "capture_browserstack.mjs"],
            returncode=0,
            stdout=json.dumps(
                {
                    "provider_id": "browserstack.playwright",
                    "provider_run_id": "run-1:iphone.webkit.real",
                    "metadata_path": str(ROOT / "tmp" / "qa-provider-test" / "capture.metadata.json"),
                    "outputs": {},
                }
            ),
            stderr="",
        )
        with mock.patch.dict(
            "os.environ",
            {
                "BROWSERSTACK_USERNAME": "atlas-browserstack-user",
                "BROWSERSTACK_ACCESS_KEY": "atlas-browserstack-key",
                "BROWSERSTACK_CAPTURE_ATTEMPTS": "2",
            },
            clear=False,
        ):
            with mock.patch(
                "ops.atlas.qa.providers.browserstack_provider.subprocess.run",
                side_effect=[failure, success],
            ) as run_mock:
                with mock.patch("ops.atlas.qa.providers.browserstack_provider.time.sleep") as sleep_mock:
                    payload = capture_with_provider(
                        root=ROOT,
                        provider_manifest_ref="ops/atlas/qa/providers/browserstack.playwright.v1.json",
                        config={
                            "repoRoot": str(ROOT / "repos" / "fawxzzy-fitness"),
                            "outputDir": str(ROOT / "tmp" / "qa-provider-test"),
                            "browserEngine": "webkit",
                            "viewport": {"width": 393, "height": 852, "device_scale_factor": 3},
                            "sourceUrl": "https://example.com",
                            "runId": "run-1",
                            "scenarioId": "fixture",
                            "adapterId": "fixture.web",
                            "repoId": "fitness",
                            "gitSha": "abcdef1234567890",
                            "lensId": "iphone.webkit.real",
                            "lensProfileId": "iphone.webkit",
                            "deviceModel": "iPhone 15",
                            "osName": "iOS",
                            "osVersion": "17",
                            "browserName": "safari",
                            "browserVersion": "17",
                        },
                    )
        self.assertEqual("run-1:iphone.webkit.real", payload["provider_run_id"])
        self.assertEqual(2, run_mock.call_count)
        sleep_mock.assert_called_once()

    def test_compatibility_report_marks_fitness_contract_compatible(self) -> None:
        report = compatibility_report(root=ROOT, adapter="fitness.web", scenario="fitness.progression-pr-smoke")
        self.assertEqual("compatible", report["status"])

    def test_compatibility_report_does_not_require_child_repo_checkout(self) -> None:
        root = self._temp_root()
        shutil.copy2(ROOT / "stack.yaml", root / "stack.yaml")
        shutil.copytree(ROOT / "schemas", root / "schemas", dirs_exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "lenses").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            ROOT / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json",
            root / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json",
        )
        shutil.copy2(
            ROOT / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json",
            root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json",
        )
        shutil.copy2(
            ROOT / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
        )
        shutil.copytree(
            ROOT / "ops" / "atlas" / "qa" / "providers",
            root / "ops" / "atlas" / "qa" / "providers",
        )

        report = compatibility_report(
            root=root,
            adapter="fitness.web",
            scenario="fitness.progression-pr-smoke",
        )

        self.assertEqual("compatible", report["status"])
        self.assertEqual([], report["findings"])

    def test_collect_test_evidence_records_passing_command(self) -> None:
        root = self._temp_root()
        repo_root = root / "repos" / "fixture"
        repo_root.mkdir(parents=True, exist_ok=True)
        scenario_path = root / "ops" / "atlas" / "qa" / "scenarios" / "fixture.contract.json"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            scenario_path,
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fixture.contract",
                "title": "fixture",
                "repo_id": "fixture",
                "repo_path": "repos/fixture",
                "adapter_id": "fixture.package",
                "criticality": "medium",
                "entrypoint": {"path": "package:root"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": [],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "manual_only",
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": ["verify"], "certify_command_sequence": []},
                "test_evidence": [
                    {
                        "evidence_id": "fixture.verify",
                        "kind": "unit",
                        "runner": "custom",
                        "command_ref": "verify",
                        "required_for": ["promotion"],
                    }
                ],
                "promotion": {
                    "require_executable_truth": True,
                    "require_pr_artifacts": True,
                    "require_real_device_on": "never",
                    "allow_manual_certification": False,
                    "max_flaky_lenses": 0,
                },
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            {
                "contract_version": "atlas.qa.lens.v1",
                "lens_set_id": "atlas-default-web",
                "title": "fixture",
                "lenses": [
                    {
                        "lens_id": "desktop.chromium",
                        "browser_engine": "chromium",
                        "viewport": {"width": 800, "height": 600, "device_scale_factor": 1},
                        "mobile": False,
                        "has_touch": False,
                    }
                ],
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "adapters" / "fixture.package.json",
            {
                "contract_version": "atlas.qa.adapter.v1",
                "adapter_id": "fixture.package",
                "repo_id": "fixture",
                "repo_path": "repos/fixture",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "commands": {
                    "verify": {
                        "command": 'python -c "print(\'1 passed\')"'
                    }
                },
                "lenses": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "profile_id": "desktop.chromium",
                        "proof_kind": "emulated",
                        "evidence_kind": "emulated_browser",
                        "required_for": ["promotion"],
                        "promotion_tier": "emulated_browser",
                        "fallback_behavior": "blocked",
                        "execution_mode": "repo_command",
                        "command_ref": "verify",
                    }
                ],
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "matrix.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("c" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "executed",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fixture.contract.json",
                "repo_id": "fixture",
                "repo_path": "repos/fixture",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fixture.package",
                "adapter_ref": "ops/atlas/qa/adapters/fixture.package.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "not_collected",
                    "certification_status": "satisfied",
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": [],
            },
        )
        result = collect_test_evidence(root=root, run_id="run-1")
        self.assertEqual("clean", result["summary"]["status"])
        self.assertEqual("passed", result["receipts"][0]["status"])

    def test_collect_test_evidence_records_failing_command(self) -> None:
        root = self._temp_root()
        repo_root = root / "repos" / "fixture"
        repo_root.mkdir(parents=True, exist_ok=True)
        scenario_path = root / "ops" / "atlas" / "qa" / "scenarios" / "fixture.contract.json"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            scenario_path,
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fixture.contract",
                "title": "fixture",
                "repo_id": "fixture",
                "repo_path": "repos/fixture",
                "adapter_id": "fixture.package",
                "criticality": "medium",
                "entrypoint": {"path": "package:root"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": [],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "manual_only",
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": ["verify"], "certify_command_sequence": []},
                "test_evidence": [
                    {
                        "evidence_id": "fixture.verify",
                        "kind": "unit",
                        "runner": "custom",
                        "command_ref": "verify",
                        "required_for": ["promotion"],
                    }
                ],
                "promotion": {
                    "require_executable_truth": True,
                    "require_pr_artifacts": True,
                    "require_real_device_on": "never",
                    "allow_manual_certification": False,
                    "max_flaky_lenses": 0,
                },
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "lenses" / "atlas-default-web.v1.json",
            {
                "contract_version": "atlas.qa.lens.v1",
                "lens_set_id": "atlas-default-web",
                "title": "fixture",
                "lenses": [
                    {
                        "lens_id": "desktop.chromium",
                        "browser_engine": "chromium",
                        "viewport": {"width": 800, "height": 600, "device_scale_factor": 1},
                        "mobile": False,
                        "has_touch": False,
                    }
                ],
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "adapters" / "fixture.package.json",
            {
                "contract_version": "atlas.qa.adapter.v1",
                "adapter_id": "fixture.package",
                "repo_id": "fixture",
                "repo_path": "repos/fixture",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "commands": {
                    "verify": {
                        "command": 'python -c "import sys; print(\'failed\'); sys.exit(2)"'
                    }
                },
                "lenses": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "profile_id": "desktop.chromium",
                        "proof_kind": "emulated",
                        "evidence_kind": "emulated_browser",
                        "required_for": ["promotion"],
                        "promotion_tier": "emulated_browser",
                        "fallback_behavior": "blocked",
                        "execution_mode": "repo_command",
                        "command_ref": "verify",
                    }
                ],
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "runs" / "run-1" / "matrix.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("d" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "executed",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fixture.contract.json",
                "repo_id": "fixture",
                "repo_path": "repos/fixture",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fixture.package",
                "adapter_ref": "ops/atlas/qa/adapters/fixture.package.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "not_collected",
                    "certification_status": "satisfied",
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0,
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": [],
            },
        )
        result = collect_test_evidence(root=root, run_id="run-1")
        self.assertEqual("failed", result["summary"]["status"])
        self.assertEqual("failed", result["receipts"][0]["status"])

    def test_baseline_propose_and_bless_reject_dry_run_and_write_manifest(self) -> None:
        root = self._temp_root()
        manifest_path, screenshot = self._base_manifest(root=root)
        run_root = manifest_path.parent
        _write_json(
            run_root / "evaluated.result.json",
            {
                "contract_version": "atlas.qa.result.v1",
                "result_id": "sha256:" + ("e" * 64),
                "generated_at": "2026-05-11T00:00:00Z",
                "runner_version": "test",
                "stage": "evaluated",
                "run_id": "run-1",
                "scenario_ref": "ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "git_sha": "abcdef1234567890",
                "adapter_id": "fitness.web",
                "adapter_ref": "ops/atlas/qa/adapters/fitness.web.json",
                "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                "mode": "execute",
                "summary": {
                    "overall_status": "ready",
                    "executable_status": "clean",
                    "artifact_status": "complete",
                    "certification_status": "satisfied",
                    "highest_satisfied_tier": "emulated_browser",
                    "satisfied_evidence_tiers": ["emulated_browser"],
                    "missing_evidence_tiers": [],
                    "manual_required_lanes": [],
                    "visual_status": "passed",
                    "visual_diff_count": 1,
                    "test_evidence_status": "clean",
                    "required_test_evidence_count": 1,
                    "lens_count": 1,
                    "failing_lens_count": 0,
                    "finding_count": 0
                },
                "matrix": [],
                "findings": [],
                "artifact_manifest_refs": [],
                "visual_diffs": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "baseline_ref": "data/atlas/qa/baselines/fitness.progression-pr-smoke/desktop.chromium.emulated.png",
                        "max_pixel_delta": 0,
                        "status": "baseline_required",
                        "evaluated_at": "2026-05-11T00:00:00Z",
                        "candidate_image_ref": "runtime/atlas/qa/runs/run-1/captures/desktop.chromium.emulated/screenshot.png"
                    }
                ]
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json",
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "title": "fixture",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "adapter_id": "fitness.web",
                "criticality": "high",
                "entrypoint": {"path": "/"},
                "proof": {
                    "pr_lenses": ["desktop.chromium.emulated"],
                    "certify_lenses": [],
                    "lens_manifest_ref": "ops/atlas/qa/lenses/atlas-default-web.v1.json",
                    "real_device_strategy": "preview_only"
                },
                "required_artifacts": [],
                "execution": {"pr_command_sequence": [], "certify_command_sequence": []},
                "visual_assertions": [
                    {
                        "lens_id": "desktop.chromium.emulated",
                        "baseline_ref": "data/atlas/qa/baselines/fitness.progression-pr-smoke/desktop.chromium.emulated.png",
                        "max_pixel_delta": 0
                    }
                ],
                "promotion": {
                    "require_executable_truth": True,
                    "require_pr_artifacts": True,
                    "require_real_device_on": "never",
                    "allow_manual_certification": False,
                    "max_flaky_lenses": 0
                }
            },
        )
        proposal = propose_baselines(root=root, run_id="run-1")
        self.assertEqual(1, proposal["proposal_count"])
        blessed = bless_baseline(root=root, run_id="run-1", lens_id="desktop.chromium.emulated", approved_by="atlas-test")
        self.assertTrue((root / blessed["baseline_manifest_ref"]).exists())

        payload = load_json_object(run_root / "evaluated.result.json")
        payload["mode"] = "dry_run"
        _write_json(run_root / "evaluated.result.json", payload)
        with self.assertRaisesRegex(ValueError, "Dry-run screenshots may not create proposed baselines"):
            propose_baselines(root=root, run_id="run-1")

    def test_evidence_index_writes_latest_files(self) -> None:
        root = self._temp_root()
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / "run-1"
        _write_json(
            run_root / "matrix.result.json",
            {
                "adapter_id": "fitness.web",
                "repo_id": "fitness",
                "git_sha": "abcdef1234567890",
                "mode": "execute"
            },
        )
        _write_json(run_root / "evaluated.result.json", {"summary": {"visual_status": "passed"}})
        _write_json(
            run_root / "promotion.record.json",
            {
                "run_id": "run-1",
                "scenario_id": "fitness.progression-pr-smoke",
                "repo_id": "fitness",
                "promotion_status": "manual_review",
                "highest_satisfied_tier": "emulated_browser",
                "missing_evidence_tiers": ["physical_device"],
                "blocking_reasons": [],
                "manual_gaps": ["physical evidence pending"]
            },
        )
        _write_json(run_root / "report.summary.json", {"ok": True})
        _write_json(run_root / "artifacts.manifest.json", {"ok": True})
        result = build_evidence_index(root=root)
        self.assertTrue((root / result["evidence_index_ref"]).exists())
        self.assertTrue((root / result["evidence_index_md_ref"]).exists())

    def test_evidence_index_adoption_prefers_meaningful_receipt_over_newer_dry_run(self) -> None:
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "fawxzzy-fitness" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        _write_json(root / "repos" / "fawxzzy-fitness" / "qa" / "adapters" / "fitness.web.json", {"ok": True})
        _write_json(root / "repos" / "fawxzzy-fitness" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json", {"ok": True})

        run_execute = root / "runtime" / "atlas" / "qa" / "runs" / "run-execute"
        _write_json(run_execute / "matrix.result.json", {"adapter_id": "fitness.web", "repo_id": "fitness", "mode": "execute"})
        _write_json(run_execute / "evaluated.result.json", {"runner_version": "atlas.qa.evaluate-run.v2", "summary": {"visual_status": "passed", "evidence_profile": "web_visual"}})
        _write_json(run_execute / "artifacts.manifest.json", {"ok": True})
        _write_json(run_execute / "promotion.record.json", {
            "run_id": "run-execute",
            "scenario_id": "fitness.progression-pr-smoke",
            "repo_id": "fitness",
            "promotion_status": "manual_review",
            "evidence_profile": "web_visual",
            "generated_at": "2026-05-11T20:00:00Z",
        })

        run_dry = root / "runtime" / "atlas" / "qa" / "runs" / "run-dry"
        _write_json(run_dry / "matrix.result.json", {"adapter_id": "fitness.web", "repo_id": "fitness", "mode": "dry_run"})
        _write_json(run_dry / "evaluated.result.json", {"runner_version": "atlas.qa.evaluate-run.v2", "summary": {"visual_status": "planned", "evidence_profile": "web_visual"}})
        _write_json(run_dry / "artifacts.manifest.json", {"ok": True})
        _write_json(run_dry / "promotion.record.json", {
            "run_id": "run-dry",
            "scenario_id": "fitness.progression-pr-smoke",
            "repo_id": "fitness",
            "promotion_status": "dry_run",
            "evidence_profile": "web_visual",
            "generated_at": "2026-05-11T21:00:00Z",
        })

        build_evidence_index(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json")
        adoption = payload["adoption"][0]
        self.assertEqual("run-execute", adoption["last_run_id"])
        self.assertEqual("manual_review", adoption["last_promotion_status"])

    def test_evidence_index_merges_root_owned_and_repo_local_contracts(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "foundation" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "foundation" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        _write_json(
            root / "ops" / "atlas" / "qa" / "adapters" / "playbook.docs.json",
            {"contract_version": "atlas.qa.adapter.v1", "adapter_id": "playbook.docs", "repo_id": "playbook"},
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "scenarios" / "playbook.docs-governance.json",
            {"contract_version": "atlas.qa.scenario.v1", "scenario_id": "playbook.docs-governance", "repo_id": "playbook"},
        )
        _write_json(
            root / "repos" / "foundation" / "qa" / "adapters" / "foundation.package.json",
            {"contract_version": "atlas.qa.adapter.v1", "adapter_id": "foundation.package", "repo_id": "foundation"},
        )
        _write_json(
            root / "repos" / "foundation" / "qa" / "scenarios" / "foundation.contract-smoke.json",
            {"contract_version": "atlas.qa.scenario.v1", "scenario_id": "foundation.contract-smoke", "repo_id": "foundation"},
        )

        build_evidence_index(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json")
        adoption_by_repo = {item["repo_id"]: item for item in payload["adoption"]}

        self.assertIn("playbook", adoption_by_repo)
        self.assertEqual(
            ["ops/atlas/qa/adapters/playbook.docs.json"],
            adoption_by_repo["playbook"]["adapter_refs"],
        )
        self.assertEqual(
            ["ops/atlas/qa/scenarios/playbook.docs-governance.json"],
            adoption_by_repo["playbook"]["scenario_refs"],
        )
        self.assertIn("foundation", adoption_by_repo)
        self.assertEqual(
            ["repos/foundation/qa/adapters/foundation.package.json"],
            adoption_by_repo["foundation"]["adapter_refs"],
        )
        self.assertEqual(
            ["repos/foundation/qa/scenarios/foundation.contract-smoke.json"],
            adoption_by_repo["foundation"]["scenario_refs"],
        )

    def test_release_readiness_applies_repo_tier_policy(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        self._write_stack_lock(root=root, components={"fitness": "fitness-target", "foundation": "foundation-target"})
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "package_contract": {
                        "display_name": "Package Contract",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_emulated", "promoted_physical", "promoted_physical_manual", "waived_promoted"]
                            }
                        },
                    },
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_physical", "promoted_physical_manual", "waived_promoted"],
                                "required_tiers": ["physical_device", "manual_attestation"],
                            }
                        },
                    },
                },
                "repo_overrides": {
                    "fitness": {"release_profile": "release_critical_web"},
                    "foundation": {"release_profile": "package_contract"},
                },
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {"run_id": "fitness-run", "repo_id": "fitness", "git_sha": "fitness-target", "promotion_generated_at": generated_at},
                    {"run_id": "foundation-run", "repo_id": "foundation", "git_sha": "foundation-target", "promotion_generated_at": generated_at},
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_git_sha": "fitness-target",
                        "last_promotion_status": "manual_review",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    },
                    {
                        "repo_id": "foundation",
                        "adopted": True,
                        "owner": "foundation",
                        "adapter_refs": ["repos/fawxzzy-foundation/qa/adapters/foundation.package.json"],
                        "scenario_refs": ["repos/fawxzzy-foundation/qa/scenarios/foundation.contract-smoke.json"],
                        "evidence_profile": "package_contract",
                        "last_run_id": "foundation-run",
                        "last_git_sha": "foundation-target",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    },
                ],
                "summary": {},
                "retention": {},
            },
        )
        result = build_release_readiness(root=root)
        self.assertTrue((root / result["release_readiness_ref"]).exists())
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repos = {item["repo_id"]: item for item in payload["repos"]}
        self.assertFalse(repos["fitness"]["release_ready"])
        self.assertEqual("manual_review", repos["fitness"]["release_gate_status"])
        self.assertTrue(repos["foundation"]["release_ready"])
        self.assertEqual("promoted_contract", repos["foundation"]["promotion_display_status"])
        self.assertTrue(repos["foundation"]["sha_match"])

    def test_release_readiness_consumes_fitness_vercel_guardrail_report(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        self._write_stack_lock(root=root, components={"fitness": "fitness-target"})
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_physical", "promoted_physical_manual", "waived_promoted"],
                                "required_tiers": ["physical_device", "manual_attestation"],
                            }
                        },
                    }
                },
                "repo_overrides": {
                    "fitness": {
                        "release_profile": "release_critical_web",
                        "governance_checks": [
                            {
                                "check_id": "fitness_vercel_hobby_guardrail",
                                "kind": "json_report",
                                "report_ref": "runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json",
                                "contract_version": "atlas.vercel_hobby_guardrail.v1",
                                "max_age_hours": 168.0,
                                "required_for_modes": ["release"],
                            }
                        ],
                    }
                },
            },
        )
        _write_json(
            root / "runtime" / "receipts" / "vercel-hobby-cost-governance" / "fitness-hobby-guardrail.latest.json",
            {
                "report_version": "atlas.vercel_hobby_guardrail.v1",
                "generated_at": generated_at,
                "summary": {"total_routes": 31, "force_dynamic_routes": 29},
                "guardrail_posture": {
                    "deployment_posture": "ok",
                    "route_pressure_posture": "watch",
                    "middleware_pressure_posture": "watch",
                    "integration_pressure_posture": "watch",
                    "hot_route_watch_posture": "watch",
                },
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {
                        "run_id": "fitness-run",
                        "repo_id": "fitness",
                        "git_sha": "fitness-target",
                        "promotion_generated_at": generated_at,
                        "promotion_status": "promoted_physical_manual",
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_git_sha": "fitness-target",
                        "last_promotion_status": "promoted_physical_manual",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )

        build_release_readiness(root=root)

        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertTrue(repo["release_ready"])
        self.assertEqual("ready", repo["release_gate_status"])
        self.assertEqual(1, len(repo["governance_checks"]))
        self.assertEqual("ready", repo["governance_checks"][0]["status"])
        self.assertEqual("ready", repo["mode_requirements"]["release"]["governance_gate_status"])

    def test_release_readiness_blocks_fitness_when_guardrail_report_missing(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        self._write_stack_lock(root=root, components={"fitness": "fitness-target"})
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_physical", "promoted_physical_manual", "waived_promoted"],
                            }
                        },
                    }
                },
                "repo_overrides": {
                    "fitness": {
                        "release_profile": "release_critical_web",
                        "governance_checks": [
                            {
                                "check_id": "fitness_vercel_hobby_guardrail",
                                "kind": "json_report",
                                "report_ref": "runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json",
                                "contract_version": "atlas.vercel_hobby_guardrail.v1",
                                "max_age_hours": 168.0,
                                "required_for_modes": ["release"],
                            }
                        ],
                    }
                },
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {
                        "run_id": "fitness-run",
                        "repo_id": "fitness",
                        "git_sha": "fitness-target",
                        "promotion_generated_at": generated_at,
                        "promotion_status": "promoted_physical_manual",
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_git_sha": "fitness-target",
                        "last_promotion_status": "promoted_physical_manual",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )

        build_release_readiness(root=root)

        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertFalse(repo["release_ready"])
        self.assertEqual("blocked", repo["release_gate_status"])
        self.assertEqual("blocked", repo["governance_checks"][0]["status"])
        self.assertEqual("blocked", repo["mode_requirements"]["release"]["governance_gate_status"])
        self.assertIn("could not load", repo["release_blockers"][0])

    def test_release_readiness_consumes_fitness_vercel_hobby_decision_checkpoint(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        self._write_stack_lock(root=root, components={"fitness": "fitness-target"})
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_physical", "promoted_physical_manual", "waived_promoted"],
                            }
                        },
                    }
                },
                "repo_overrides": {
                    "fitness": {
                        "release_profile": "release_critical_web",
                        "governance_checks": [
                            {
                                "check_id": "fitness_vercel_hobby_decision",
                                "kind": "json_report",
                                "report_ref": "runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.json",
                                "contract_version": "atlas.vercel_hobby_decision.v1",
                                "max_age_hours": 168.0,
                                "required_for_modes": ["release"],
                            }
                        ],
                    }
                },
            },
        )
        _write_json(
            root / "runtime" / "receipts" / "vercel-hobby-cost-governance" / "fitness-hobby-decision.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_decision.v1",
                "generated_at": generated_at,
                "checkpoint_status": "ready",
                "decision": "keep_hobby",
                "decision_reason": "stable preserved trend and aligned rolling latest",
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {
                        "run_id": "fitness-run",
                        "repo_id": "fitness",
                        "git_sha": "fitness-target",
                        "promotion_generated_at": generated_at,
                        "promotion_status": "promoted_physical_manual",
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_git_sha": "fitness-target",
                        "last_promotion_status": "promoted_physical_manual",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )

        build_release_readiness(root=root)

        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertTrue(repo["release_ready"])
        self.assertEqual("ready", repo["release_gate_status"])
        self.assertEqual("keep_hobby", repo["governance_checks"][0]["decision"])
        self.assertEqual("ready", repo["governance_checks"][0]["checkpoint_status"])

    def test_release_readiness_blocks_when_hobby_decision_checkpoint_requires_review(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        self._write_stack_lock(root=root, components={"fitness": "fitness-target"})
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_physical", "promoted_physical_manual", "waived_promoted"],
                            }
                        },
                    }
                },
                "repo_overrides": {
                    "fitness": {
                        "release_profile": "release_critical_web",
                        "governance_checks": [
                            {
                                "check_id": "fitness_vercel_hobby_decision",
                                "kind": "json_report",
                                "report_ref": "runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.json",
                                "contract_version": "atlas.vercel_hobby_decision.v1",
                                "max_age_hours": 168.0,
                                "required_for_modes": ["release"],
                            }
                        ],
                    }
                },
            },
        )
        _write_json(
            root / "runtime" / "receipts" / "vercel-hobby-cost-governance" / "fitness-hobby-decision.latest.json",
            {
                "contract_version": "atlas.vercel_hobby_decision.v1",
                "generated_at": generated_at,
                "checkpoint_status": "blocked",
                "decision": "upgrade_review_required",
                "decision_reason": "preserved route pressure drift detected",
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {
                        "run_id": "fitness-run",
                        "repo_id": "fitness",
                        "git_sha": "fitness-target",
                        "promotion_generated_at": generated_at,
                        "promotion_status": "promoted_physical_manual",
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_git_sha": "fitness-target",
                        "last_promotion_status": "promoted_physical_manual",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )

        build_release_readiness(root=root)

        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertFalse(repo["release_ready"])
        self.assertEqual("blocked", repo["release_gate_status"])
        self.assertEqual("blocked", repo["governance_checks"][0]["status"])
        self.assertIn("upgrade_review_required", repo["mode_requirements"]["release"]["governance_blockers"][0])

    def test_release_readiness_reports_stale_receipt_age(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "package_contract": {
                        "display_name": "Package Contract",
                        "mode_requirements": {
                            "release": {"allowed_statuses": ["promoted_emulated"]}
                        },
                    }
                },
                "repo_overrides": {"foundation": {"release_profile": "package_contract"}},
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "runs": [
                    {
                        "run_id": "foundation-run",
                        "repo_id": "foundation",
                        "promotion_generated_at": "2000-01-01T00:00:00Z",
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "foundation",
                        "adopted": True,
                        "owner": "foundation",
                        "adapter_refs": ["repos/fawxzzy-foundation/qa/adapters/foundation.package.json"],
                        "scenario_refs": ["repos/fawxzzy-foundation/qa/scenarios/foundation.contract-smoke.json"],
                        "evidence_profile": "package_contract",
                        "last_run_id": "foundation-run",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        build_release_readiness(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        self.assertGreater(payload["repos"][0]["last_receipt_age_hours"], 1)

    def test_release_readiness_marks_non_release_eligible_repo_not_applicable(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        (root / "stack.lock.yaml").write_text(
            "\n".join(
                [
                    'schema_version: "atlas.stack.lock.v1"',
                    "components:",
                    "  stream:",
                    '    commit: "stream-target"',
                    "    remote: null",
                    "    release_eligible: false",
                ]
            ) + "\n",
            encoding="utf-8",
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "package_contract": {
                        "display_name": "Package Contract",
                        "require_trusted_origin": True,
                        "enforcement_stage": "enforce",
                        "allowed_release_origins": ["protected_manual"],
                        "mode_requirements": {
                            "release": {"allowed_statuses": ["promoted_emulated"]}
                        },
                    }
                },
                "repo_overrides": {"stream": {"release_profile": "package_contract"}},
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-06-27T07:41:33Z",
                "runs": [
                    {
                        "run_id": "stream-run",
                        "repo_id": "stream",
                        "git_sha": "stream-target",
                        "promotion_generated_at": "2026-06-27T07:41:33Z",
                        "promotion_status": "promoted_emulated",
                        "receipt_origin": {"origin_type": "local_dev"},
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "stream",
                        "adopted": True,
                        "owner": "stream",
                        "adapter_refs": ["repos/stream/qa/adapters/stream.package.json"],
                        "scenario_refs": ["repos/stream/qa/scenarios/stream.contract-smoke.json"],
                        "evidence_profile": "package_contract",
                        "last_run_id": "stream-run",
                        "last_git_sha": "stream-target",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )

        build_release_readiness(root=root)

        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertFalse(repo["release_eligible"])
        self.assertEqual("not_applicable", repo["release_scope_status"])
        self.assertEqual("not_applicable", repo["release_gate_status"])
        self.assertFalse(repo["release_ready"])
        self.assertEqual([], repo["release_blockers"])
        self.assertEqual(0, payload["summary"]["blocked_count"])
        self.assertEqual(1, payload["summary"]["not_applicable_count"])

    def test_build_receipt_origin_ignores_trusted_override_outside_github_actions(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "ATLAS_QA_ORIGIN_TYPE": "protected_manual",
                "GITHUB_ACTIONS": "false",
            },
            clear=False,
        ):
            origin = build_receipt_origin(
                runner_version="atlas.qa.promote-run.v3",
                repo_id="fitness",
                git_sha="target-sha",
                command="python ops/atlas/qa/promote_run.py",
                origin_type="ci_release",
            )
        self.assertEqual("local_dev", origin["origin_type"])

    def test_build_receipt_origin_accepts_workflow_dispatch_inside_github_actions(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "ATLAS_QA_ORIGIN_TYPE": "",
                "GITHUB_ACTIONS": "true",
                "GITHUB_EVENT_NAME": "workflow_dispatch",
            },
            clear=False,
        ):
            origin = build_receipt_origin(
                runner_version="atlas.qa.promote-run.v3",
                repo_id="fitness",
                git_sha="target-sha",
                command="python ops/atlas/qa/promote_run.py",
            )
        self.assertEqual("protected_manual", origin["origin_type"])

    def test_release_readiness_blocks_wrong_target_sha(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._write_stack_lock(root=root, components={"playbook": "target-sha"})
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "docs_governance": {
                        "display_name": "Docs Governance",
                        "mode_requirements": {
                            "release": {"allowed_statuses": ["promoted_emulated"]}
                        },
                    }
                },
                "repo_overrides": {"playbook": {"release_profile": "docs_governance"}},
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {
                        "run_id": "playbook-run",
                        "repo_id": "playbook",
                        "git_sha": "wrong-sha",
                        "promotion_generated_at": generated_at,
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "playbook",
                        "adopted": True,
                        "owner": "playbook",
                        "adapter_refs": ["repos/fawxzzy-playbook/qa/adapters/playbook.docs.json"],
                        "scenario_refs": ["repos/fawxzzy-playbook/qa/scenarios/playbook.docs-governance.json"],
                        "evidence_profile": "docs_governance",
                        "last_run_id": "playbook-run",
                        "last_git_sha": "wrong-sha",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        build_release_readiness(root=root, target_sha="target-sha")
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertFalse(repo["release_ready"])
        self.assertFalse(repo["sha_match"])
        self.assertIn("wrong SHA", repo["release_blockers"][0])

    def test_release_readiness_blocks_untrusted_origin_when_policy_enabled(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._write_stack_lock(root=root, components={"playbook": "target-sha"})
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "docs_governance": {
                        "display_name": "Docs Governance",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_emulated"],
                                "trusted_origins": ["ci_release", "protected_manual"],
                            }
                        },
                    }
                },
                "repo_overrides": {"playbook": {"release_profile": "docs_governance"}},
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {
                        "run_id": "playbook-run",
                        "repo_id": "playbook",
                        "git_sha": "target-sha",
                        "promotion_generated_at": generated_at,
                        "receipt_origin": {
                            "origin_type": "local_dev",
                            "actor": "atlas-local",
                            "workflow_name": "",
                            "workflow_run_id": "",
                            "command": "python ops/atlas/qa/ci_gate.py --mode promotion",
                            "runner_os": "Windows",
                            "generated_at": generated_at,
                            "repo": "playbook",
                            "git_sha": "target-sha",
                            "stack_lock_hash": "sha256:" + ("a" * 64),
                            "qa_runner_version": "atlas.qa.promote-run.v3",
                        },
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "playbook",
                        "adopted": True,
                        "owner": "playbook",
                        "adapter_refs": ["repos/fawxzzy-playbook/qa/adapters/playbook.docs.json"],
                        "scenario_refs": ["repos/fawxzzy-playbook/qa/scenarios/playbook.docs-governance.json"],
                        "evidence_profile": "docs_governance",
                        "last_run_id": "playbook-run",
                        "last_git_sha": "target-sha",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        build_release_readiness(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertFalse(repo["release_ready"])
        self.assertEqual("local_dev", repo["receipt_origin_type"])
        self.assertTrue(repo["trusted_origin_required"])
        self.assertEqual(["ci_release", "protected_manual"], repo["allowed_release_origins"])
        self.assertEqual("enforce", repo["origin_enforcement_stage"])
        self.assertEqual("blocked", repo["trusted_origin_status"])
        self.assertFalse(repo["trusted_origin_match"])
        self.assertIn("not trusted", repo["release_blockers"][0])

    def test_release_readiness_warn_stage_reports_untrusted_origin_without_blocking(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._write_stack_lock(root=root, components={"playbook": "target-sha"})
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "docs_governance": {
                        "display_name": "Docs Governance",
                        "require_trusted_origin": True,
                        "allowed_release_origins": ["ci_release", "protected_manual"],
                        "allowed_pr_origins": ["ci_pr", "local_dev"],
                        "enforcement_stage": "warn",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_emulated"],
                            }
                        },
                    }
                },
                "repo_overrides": {"playbook": {"release_profile": "docs_governance"}},
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {
                        "run_id": "playbook-run",
                        "repo_id": "playbook",
                        "git_sha": "target-sha",
                        "promotion_generated_at": generated_at,
                        "receipt_origin": {
                            "origin_type": "local_dev",
                            "actor": "atlas-local",
                            "workflow_name": "",
                            "workflow_run_id": "",
                            "command": "python ops/atlas/qa/ci_gate.py --mode promotion",
                            "runner_os": "Windows",
                            "generated_at": generated_at,
                            "repo": "playbook",
                            "git_sha": "target-sha",
                            "stack_lock_hash": "sha256:" + ("a" * 64),
                            "qa_runner_version": "atlas.qa.promote-run.v3",
                        },
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "playbook",
                        "adopted": True,
                        "owner": "playbook",
                        "adapter_refs": ["repos/fawxzzy-playbook/qa/adapters/playbook.docs.json"],
                        "scenario_refs": ["repos/fawxzzy-playbook/qa/scenarios/playbook.docs-governance.json"],
                        "evidence_profile": "docs_governance",
                        "last_run_id": "playbook-run",
                        "last_git_sha": "target-sha",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        build_release_readiness(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertTrue(repo["release_ready"])
        self.assertEqual("warn", repo["origin_enforcement_stage"])
        self.assertEqual("warn", repo["trusted_origin_status"])
        self.assertFalse(repo["trusted_origin_match"])
        self.assertEqual([], repo["release_blockers"])

    def test_release_readiness_prefers_stronger_trusted_receipt_over_newer_local(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        trusted_generated_at = datetime.now(timezone.utc).replace(microsecond=0)
        local_generated_at = trusted_generated_at + timedelta(minutes=30)
        trusted_generated_at_text = trusted_generated_at.isoformat().replace("+00:00", "Z")
        local_generated_at_text = local_generated_at.isoformat().replace("+00:00", "Z")
        self._write_stack_lock(root=root, components={"playbook": "target-sha"})
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "docs_governance": {
                        "display_name": "Docs Governance",
                        "require_trusted_origin": True,
                        "allowed_release_origins": ["ci_release", "protected_manual"],
                        "allowed_pr_origins": ["ci_pr", "local_dev"],
                        "enforcement_stage": "warn",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["promoted_emulated"],
                            }
                        },
                    }
                },
                "repo_overrides": {"playbook": {"release_profile": "docs_governance"}},
            },
        )
        trusted_origin = {
            "origin_type": "ci_release",
            "actor": "atlas-ci",
            "workflow_name": "ATLAS QA LLEL",
            "workflow_run_id": "1234",
            "command": "python ops/atlas/qa/ci_gate.py --mode promotion",
            "runner_os": "Linux",
            "generated_at": trusted_generated_at_text,
            "repo": "playbook",
            "git_sha": "target-sha",
            "stack_lock_hash": "sha256:" + ("b" * 64),
            "qa_runner_version": "atlas.qa.promote-run.v3",
        }
        local_origin = {
            "origin_type": "local_dev",
            "actor": "atlas-local",
            "workflow_name": "",
            "workflow_run_id": "",
            "command": "python ops/atlas/qa/ci_gate.py --mode promotion",
            "runner_os": "Windows",
            "generated_at": local_generated_at_text,
            "repo": "playbook",
            "git_sha": "target-sha",
            "stack_lock_hash": "sha256:" + ("c" * 64),
            "qa_runner_version": "atlas.qa.promote-run.v3",
        }
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": local_generated_at_text,
                "runs": [
                    {
                        "run_id": "playbook-trusted",
                        "repo_id": "playbook",
                        "git_sha": "target-sha",
                        "promotion_generated_at": trusted_generated_at_text,
                        "promotion_status": "promoted_emulated",
                        "evidence_profile": "docs_governance",
                        "receipt_origin": trusted_origin,
                    },
                    {
                        "run_id": "playbook-local",
                        "repo_id": "playbook",
                        "git_sha": "target-sha",
                        "promotion_generated_at": local_generated_at_text,
                        "promotion_status": "promoted_emulated",
                        "evidence_profile": "docs_governance",
                        "receipt_origin": local_origin,
                    },
                ],
                "adoption": [
                    {
                        "repo_id": "playbook",
                        "adopted": True,
                        "owner": "playbook",
                        "adapter_refs": ["repos/fawxzzy-playbook/qa/adapters/playbook.docs.json"],
                        "scenario_refs": ["repos/fawxzzy-playbook/qa/scenarios/playbook.docs-governance.json"],
                        "evidence_profile": "docs_governance",
                        "last_run_id": "playbook-local",
                        "last_git_sha": "target-sha",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        build_release_readiness(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertEqual("playbook-trusted", repo["readiness_source_run_id"])
        self.assertEqual("playbook-local", repo["selection_newest_run_id"])
        self.assertEqual("ci_release", repo["receipt_origin_type"])
        self.assertIn("stronger trusted origin", repo["selection_reason"])

    def test_release_readiness_revalidates_waiver_expiry(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        self._write_stack_lock(root=root, components={"fitness": "target-sha"})
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "mode_requirements": {
                            "release": {
                                "allowed_statuses": ["waived_promoted"],
                            }
                        },
                    }
                },
                "repo_overrides": {"fitness": {"release_profile": "release_critical_web"}},
            },
        )
        waiver_path = _write_waiver(root=root, run_id="fitness-run", expires_at="2000-01-01T00:00:00Z")
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "runs": [
                    {
                        "run_id": "fitness-run",
                        "repo_id": "fitness",
                        "scenario_id": "fitness.progression-pr-smoke",
                        "git_sha": "target-sha",
                        "promotion_generated_at": "2026-05-11T00:00:00Z",
                        "promotion_status": "waived_promoted",
                        "evidence_profile": "web_visual",
                        "waived_lanes": ["android.chrome.real.manual"],
                        "waiver_refs": [str(waiver_path.relative_to(root).as_posix())],
                        "receipt_origin": {
                            "origin_type": "local_dev",
                            "actor": "atlas-local",
                            "workflow_name": "",
                            "workflow_run_id": "",
                            "command": "python ops/atlas/qa/promote_run.py",
                            "runner_os": "Windows",
                            "generated_at": "2026-05-11T00:00:00Z",
                            "repo": "fitness",
                            "git_sha": "target-sha",
                            "stack_lock_hash": "sha256:" + ("a" * 64),
                            "qa_runner_version": "atlas.qa.promote-run.v3",
                        },
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_git_sha": "target-sha",
                        "last_promotion_status": "waived_promoted",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        build_release_readiness(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-readiness.latest.json")
        repo = payload["repos"][0]
        self.assertFalse(repo["release_ready"])
        self.assertFalse(repo["release_ready_with_waiver"])
        self.assertIn("expired", repo["release_blockers"][0])

    def test_waiver_monitor_reports_active_and_expired_waivers(self) -> None:
        root = self._temp_root()
        _write_waiver(root=root, run_id="run-1", expires_at="2099-01-01T00:00:00Z")
        _write_waiver(root=root, run_id="run-2", expires_at="2000-01-01T00:00:00Z")
        result = build_waiver_monitor(root=root)
        self.assertTrue((root / result["waiver_monitor_ref"]).exists())
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "waiver-monitor.latest.json")
        statuses = {item["run_id"]: item["status"] for item in payload["waivers"]}
        self.assertEqual("active", statuses["run-1"])
        self.assertEqual("expired", statuses["run-2"])

    def test_materialize_runtime_waivers_reissues_matching_spec(self) -> None:
        root = self._temp_root()
        created = _materialize_runtime_waivers(
            root=root,
            run_id="run-2",
            repo_id="fitness",
            scenario_id="fitness.progression-pr-smoke",
            waiver_specs=[
                {
                    "repo_id": "fitness",
                    "scenario_id": "fitness.progression-pr-smoke",
                    "waived_lane": "android.chrome.real.manual",
                    "reason": "Android device/provider unavailable in current operator environment",
                    "expires_at": "2026-05-19T23:59:59Z",
                    "evidence_present": [
                        "desktop.chromium.real.manual",
                        "iphone.webkit.real.manual",
                        "android.chrome.emulated",
                    ],
                    "limitation": "Android physical proof was not captured",
                },
                {
                    "repo_id": "playbook",
                    "scenario_id": "playbook.docs-governance",
                    "waived_lane": "desktop.chromium.real.manual",
                    "reason": "wrong repo",
                    "expires_at": "2026-05-19T23:59:59Z",
                    "evidence_present": ["desktop.chromium.emulated"],
                    "limitation": "n/a",
                },
            ],
        )
        self.assertEqual(1, len(created))
        payload = load_json_object(Path(created[0]))
        self.assertEqual("run-2", payload["run_id"])
        self.assertEqual("fitness", payload["repo_id"])
        self.assertEqual("fitness.progression-pr-smoke", payload["scenario_id"])
        self.assertEqual("android.chrome.real.manual", payload["waived_lane"])

    def test_protected_release_refresh_runs_target_repo_and_writes_report(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {"release_critical_web": {"display_name": "Release-Critical Web"}},
                "repo_overrides": {"fitness": {"release_profile": "release_critical_web"}},
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json",
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "repo_id": "fitness",
                "adapter_id": "fitness.web",
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "adapters" / "fitness.web.json",
            {
                "contract_version": "atlas.qa.adapter.v1",
                "adapter_id": "fitness.web",
                "repo_id": "fitness",
            },
        )
        waiver_specs = [
            {
                "repo_id": "fitness",
                "scenario_id": "fitness.progression-pr-smoke",
                "waived_lane": "android.chrome.real.manual",
                "reason": "Android device/provider unavailable in current operator environment",
                "expires_at": "2026-05-19T23:59:59Z",
                "evidence_present": ["android.chrome.emulated"],
                "limitation": "Android physical proof was not captured",
            }
        ]
        with (
            mock.patch(
                "ops.atlas.qa.protected_release_refresh.ci_gate",
                return_value={
                    "run_id": "fitness-run",
                    "promotion": {
                        "promotion_status": "waived_promoted",
                        "receipt_origin": {"origin_type": "protected_manual"},
                    },
                    "waivers": ["runtime/atlas/qa/runs/fitness-run/waivers/android.chrome.real.manual.waiver.json"],
                },
            ) as ci_gate_mock,
            mock.patch("ops.atlas.qa.protected_release_refresh.build_evidence_index", return_value={"evidence_index_ref": "runtime/atlas/qa/evidence-index.latest.json"}),
            mock.patch("ops.atlas.qa.protected_release_refresh.build_waiver_monitor", return_value={"waiver_monitor_ref": "runtime/atlas/qa/waiver-monitor.latest.json"}),
            mock.patch("ops.atlas.qa.protected_release_refresh.build_adoption_drift", return_value={"adoption_drift_ref": "runtime/atlas/qa/adoption-drift.latest.json"}),
            mock.patch("ops.atlas.qa.protected_release_refresh.build_release_readiness", return_value={"release_readiness_ref": "runtime/atlas/qa/release-readiness.latest.json"}),
            mock.patch("ops.atlas.qa.protected_release_refresh.build_release_rehearsal", return_value={"release_rehearsal_ref": "runtime/atlas/qa/release-rehearsal.latest.json"}),
        ):
            result = refresh_protected_release_receipts(root=root, repo_ids=["fitness"], waiver_specs=waiver_specs)
        self.assertTrue((root / result["protected_release_refresh_ref"]).exists())
        ci_gate_mock.assert_called_once_with(
            root=root.resolve(),
            mode="promotion",
            scenario="fitness.progression-pr-smoke",
            adapter="fitness.web",
            provider=None,
            waiver_specs=waiver_specs,
            allow_missing_locked_repos=True,
            required_present_repo_ids=["fitness"],
        )

    def test_bootstrap_release_repos_clones_exact_locked_commit(self) -> None:
        root = self._temp_root()
        source_repo = root / "fixtures" / "playbook-remote"
        commit = _init_committed_repo(source_repo, content="# playbook\n")
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {"docs_governance": {"display_name": "Docs Governance"}},
                "repo_overrides": {"playbook": {"release_profile": "docs_governance"}},
            },
        )
        (root / "stack.lock.yaml").write_text(
            "\n".join(
                [
                    'schema_version: "atlas.stack.lock.v1"',
                    'stack_manifest_path: "stack.yaml"',
                    'stack_manifest_digest: "sha256:' + ("a" * 64) + '"',
                    "component_count: 1",
                    "components:",
                    "  playbook:",
                    '    path: "repos/fawxzzy-playbook"',
                    '    role: "docs"',
                    '    status: "active"',
                    f'    remote: "{source_repo.as_posix()}"',
                    '    ref_type: "commit"',
                    f'    ref: "{commit}"',
                    f'    commit: "{commit}"',
                    "    dirty: false",
                    '    trust_class: "trusted"',
                    "    release_eligible: true",
                    "excluded_surfaces: {}",
                    'lock_digest: "sha256:' + ("b" * 64) + '"',
                ]
            ) + "\n",
            encoding="utf-8",
        )
        result = bootstrap_release_repos(root=root, repo_ids=["playbook"])
        self.assertTrue((root / result["bootstrap_release_repos_ref"]).exists())
        target_repo = root / "repos" / "fawxzzy-playbook"
        self.assertTrue(target_repo.exists())
        self.assertEqual(commit, _git(target_repo, "rev-parse", "HEAD"))

    def test_bootstrap_release_repos_fails_for_dirty_release_target(self) -> None:
        root = self._temp_root()
        source_repo = root / "fixtures" / "playbook-remote"
        commit = _init_committed_repo(source_repo, content="# playbook\n")
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {"docs_governance": {"display_name": "Docs Governance"}},
                "repo_overrides": {"playbook": {"release_profile": "docs_governance"}},
            },
        )
        (root / "stack.lock.yaml").write_text(
            "\n".join(
                [
                    'schema_version: "atlas.stack.lock.v1"',
                    'stack_manifest_path: "stack.yaml"',
                    'stack_manifest_digest: "sha256:' + ("a" * 64) + '"',
                    "component_count: 1",
                    "components:",
                    "  playbook:",
                    '    path: "repos/fawxzzy-playbook"',
                    '    role: "docs"',
                    '    status: "active"',
                    f'    remote: "{source_repo.as_posix()}"',
                    '    ref_type: "commit"',
                    f'    ref: "{commit}"',
                    f'    commit: "{commit}"',
                    "    dirty: true",
                    '    trust_class: "trusted"',
                    "    release_eligible: true",
                    "excluded_surfaces: {}",
                    'lock_digest: "sha256:' + ("b" * 64) + '"',
                ]
            ) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(SystemExit) as exc:
            bootstrap_release_repos(root=root, repo_ids=["playbook"])
        self.assertIn("dirty", str(exc.exception))

    def test_atlas_qa_workflow_uses_canonical_release_repo_paths(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "atlas-qa-llel.yml").read_text(encoding="utf-8")
        self.assertIn("working-directory: repos/playbook", workflow)
        self.assertIn("working-directory: repos/foundation", workflow)
        self.assertIn("working-directory: repos/lifeline", workflow)
        self.assertNotIn("working-directory: repos/fawxzzy-playbook", workflow)
        self.assertNotIn("working-directory: repos/fawxzzy-foundation", workflow)
        self.assertNotIn("working-directory: repos/fawxzzy-lifeline", workflow)

    def test_release_snapshot_copies_fitness_waiver_pack(self) -> None:
        root = self._temp_root()
        snapshot_run = "run-1"
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / snapshot_run
        _write_json(
            run_root / "promotion.record.json",
            {
                "contract_version": "atlas.qa.promotion.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "promotion_id": "sha256:" + ("a" * 64),
                "evaluator_version": "atlas.qa.promote-run.v3",
                "run_id": snapshot_run,
                "scenario_id": "fitness.progression-pr-smoke",
                "repo_id": "fitness",
                "criticality": "high",
                "promotion_status": "waived_promoted",
                "evidence_profile": "web_visual",
                "highest_satisfied_tier": "emulated_browser",
                "satisfied_evidence_tiers": ["emulated_browser"],
                "missing_evidence_tiers": ["physical_device"],
                "manual_required_lanes": [],
                "waived_lanes": ["android.chrome.real.manual"],
                "waiver_refs": [f"runtime/atlas/qa/runs/{snapshot_run}/waivers/android.chrome.real.manual.waiver.json"],
                "waiver_reasons": ["Android device/provider unavailable in current operator environment"],
                "decision": "promote",
                "summary": {
                    "executable_truth": "clean",
                    "artifact_coverage": "complete",
                    "real_device_proof": "waived",
                    "visual_status": "passed",
                    "test_evidence_status": "clean",
                    "evidence_profile": "web_visual",
                    "governance_status": "clean",
                    "flake_status": "none"
                },
                "blocking_reasons": [],
                "manual_gaps": [],
                "governance": {"status": "clean", "critical_count": 0, "error_count": 0},
                "source_refs": {
                    "scenario_ref": "repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json",
                    "result_ref": f"runtime/atlas/qa/runs/{snapshot_run}/evaluated.result.json",
                    "artifact_refs": [f"runtime/atlas/qa/runs/{snapshot_run}/artifacts.manifest.json"]
                },
                "operator_summary": ["waived"],
                "receipt_origin": {
                    "origin_type": "local_dev",
                    "actor": "atlas-local",
                    "workflow_name": "",
                    "workflow_run_id": "",
                    "command": "python ops/atlas/qa/promote_run.py",
                    "runner_os": "Windows",
                    "generated_at": "2026-05-12T00:00:00Z",
                    "repo": "fitness",
                    "git_sha": "target-sha",
                    "stack_lock_hash": "sha256:" + ("a" * 64),
                    "qa_runner_version": "atlas.qa.promote-run.v3"
                }
            },
        )
        _write_json(
            run_root / "report.summary.json",
            {
                "contract_version": "atlas.qa.report.v1",
                "run_id": snapshot_run,
                "promotion_status": "waived_promoted",
                "waived_lanes": ["android.chrome.real.manual"],
                "per_lens": [
                    {"lens_id": "desktop.chromium.emulated", "status": "pass"},
                    {"lens_id": "android.chrome.emulated", "status": "pass"},
                    {"lens_id": "iphone.webkit.emulated", "status": "pass"},
                    {"lens_id": "android.chrome.real", "status": "manual_required"},
                ],
            },
        )
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", {"summary": {"critical": 0, "error": 0, "warning": 1}})
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-warning-budget.latest.json", {"warning_count": 1})
        _write_waiver(root=root, run_id=snapshot_run)
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "runs": [
                    {
                        "run_id": snapshot_run,
                        "repo_id": "fitness",
                        "scenario_id": "fitness.progression-pr-smoke",
                        "git_sha": "target-sha",
                        "promotion_generated_at": "2026-05-12T00:00:00Z",
                        "promotion_status": "waived_promoted",
                        "evidence_profile": "web_visual",
                        "waived_lanes": ["android.chrome.real.manual"],
                        "waiver_refs": [f"runtime/atlas/qa/runs/{snapshot_run}/waivers/android.chrome.real.manual.waiver.json"],
                        "receipt_origin": {
                            "origin_type": "local_dev",
                            "actor": "atlas-local",
                            "workflow_name": "",
                            "workflow_run_id": "",
                            "command": "python ops/atlas/qa/promote_run.py",
                            "runner_os": "Windows",
                            "generated_at": "2026-05-12T00:00:00Z",
                            "repo": "fitness",
                            "git_sha": "target-sha",
                            "stack_lock_hash": "sha256:" + ("a" * 64),
                            "qa_runner_version": "atlas.qa.promote-run.v3"
                        }
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": snapshot_run,
                        "last_git_sha": "target-sha",
                        "last_promotion_status": "waived_promoted",
                        "last_promotion_display_status": "waived_promoted",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                        "receipt_origin_type": "local_dev",
                        "waived_lanes": ["android.chrome.real.manual"]
                    }
                ],
                "summary": {},
                "retention": {}
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "require_trusted_origin": True,
                        "allowed_release_origins": ["ci_release", "protected_manual", "provider"],
                        "allowed_pr_origins": ["ci_pr", "local_dev"],
                        "enforcement_stage": "warn",
                        "mode_requirements": {"release": {"allowed_statuses": ["waived_promoted"]}}
                    }
                },
                "repo_overrides": {"fitness": {"release_profile": "release_critical_web"}}
            },
        )
        self._write_stack_lock(root=root, components={"fitness": "target-sha"})
        build_release_readiness(root=root)
        result = build_release_snapshot(root=root, repo_id="fitness")
        self.assertTrue((root / result["snapshot_summary_ref"]).exists())
        payload = load_json_object(root / result["snapshot_summary_ref"])
        self.assertTrue(payload["release_ready_with_waiver"])
        self.assertEqual(["android.chrome.real.manual"], payload["waived_lanes"])
        self.assertEqual(
            ["android.chrome.emulated", "desktop.chromium.emulated", "iphone.webkit.emulated"],
            payload["evidence_present"],
        )
        self.assertEqual(["android.chrome.real.manual"], payload["evidence_missing"])

    def test_release_snapshot_derives_valid_manual_attestation_and_missing_lanes(self) -> None:
        root = self._temp_root()
        snapshot_run = "run-1"
        run_root = root / "runtime" / "atlas" / "qa" / "runs" / snapshot_run
        _write_json(
            run_root / "promotion.record.json",
            {
                "contract_version": "atlas.qa.promotion.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "promotion_id": "sha256:" + ("b" * 64),
                "evaluator_version": "atlas.qa.promote-run.v3",
                "run_id": snapshot_run,
                "scenario_id": "fitness.progression-pr-smoke",
                "repo_id": "fitness",
                "criticality": "high",
                "promotion_status": "manual_review",
                "evidence_profile": "web_visual",
                "highest_satisfied_tier": "emulated_browser",
                "satisfied_evidence_tiers": ["emulated_browser"],
                "missing_evidence_tiers": ["physical_device"],
                "manual_required_lanes": ["android.chrome.real", "iphone.webkit.real"],
                "waived_lanes": [],
                "waiver_refs": [],
                "waiver_reasons": [],
                "decision": "manual_review",
                "summary": {
                    "executable_truth": "clean",
                    "artifact_coverage": "complete",
                    "real_device_proof": "manual_required",
                    "visual_status": "passed",
                    "test_evidence_status": "clean",
                    "evidence_profile": "web_visual",
                    "governance_status": "clean",
                    "flake_status": "none",
                },
                "blocking_reasons": [],
                "manual_gaps": ["Real-device certification still requires manual completion."],
                "governance": {"status": "clean", "critical_count": 0, "error_count": 0},
                "source_refs": {
                    "scenario_ref": "repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json",
                    "result_ref": f"runtime/atlas/qa/runs/{snapshot_run}/evaluated.result.json",
                    "artifact_refs": [f"runtime/atlas/qa/runs/{snapshot_run}/artifacts.manifest.json"],
                },
                "operator_summary": ["Manual review required before promotion."],
                "receipt_origin": {
                    "origin_type": "local_dev",
                    "actor": "atlas-local",
                    "workflow_name": "",
                    "workflow_run_id": "",
                    "command": "python ops/atlas/qa/promote_run.py",
                    "runner_os": "Windows",
                    "generated_at": "2026-05-12T00:00:00Z",
                    "repo": "fitness",
                    "git_sha": "target-sha",
                    "stack_lock_hash": "sha256:" + ("a" * 64),
                    "qa_runner_version": "atlas.qa.promote-run.v3",
                },
            },
        )
        _write_json(
            run_root / "report.summary.json",
            {
                "contract_version": "atlas.qa.report.v1",
                "run_id": snapshot_run,
                "promotion_status": "manual_review",
                "manual_required_lanes": [
                    "desktop.chromium.real",
                    "android.chrome.real",
                    "iphone.webkit.real",
                ],
                "waived_lanes": [],
                "per_lens": [
                    {"lens_id": "desktop.chromium.emulated", "status": "pass"},
                    {"lens_id": "android.chrome.emulated", "status": "pass"},
                    {"lens_id": "iphone.webkit.emulated", "status": "pass"},
                    {"lens_id": "desktop.chromium.real", "status": "manual_required"},
                    {"lens_id": "android.chrome.real", "status": "manual_required"},
                    {"lens_id": "iphone.webkit.real", "status": "manual_required"},
                ],
            },
        )
        _write_json(
            run_root / "manual_attestation.result.json",
            {
                "runner_version": "atlas.qa.manual-attestation.validate.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "run_id": snapshot_run,
                "status": "invalid",
                "attestation_count": 3,
                "attestations": [
                    {
                        "attestation_id": f"{snapshot_run}:desktop.chromium.real:manual",
                        "attestation_ref": f"runtime/atlas/qa/runs/{snapshot_run}/manual-attestations/desktop.chromium.real.manual.json",
                        "run_id": snapshot_run,
                        "scenario_id": "fitness.progression-pr-smoke",
                        "adapter_id": "fitness.web",
                        "lens_id": "desktop.chromium.real",
                        "operator": "atlas-operator",
                        "capture_method": "manual_attestation",
                        "status": "valid",
                    },
                    {
                        "attestation_id": f"{snapshot_run}:android.chrome.real:manual",
                        "attestation_ref": f"runtime/atlas/qa/runs/{snapshot_run}/manual-attestations/android.chrome.real.manual.json",
                        "run_id": snapshot_run,
                        "scenario_id": "fitness.progression-pr-smoke",
                        "adapter_id": "fitness.web",
                        "lens_id": "android.chrome.real",
                        "operator": "atlas-operator",
                        "capture_method": "manual_attestation",
                        "status": "invalid",
                    },
                    {
                        "attestation_id": f"{snapshot_run}:iphone.webkit.real:manual",
                        "attestation_ref": f"runtime/atlas/qa/runs/{snapshot_run}/manual-attestations/iphone.webkit.real.manual.json",
                        "run_id": snapshot_run,
                        "scenario_id": "fitness.progression-pr-smoke",
                        "adapter_id": "fitness.web",
                        "lens_id": "iphone.webkit.real",
                        "operator": "atlas-operator",
                        "capture_method": "manual_attestation",
                        "status": "invalid",
                    },
                ],
                "finding_count": 2,
                "findings": [
                    {"severity": "error", "code": "missing_attestation_screenshot", "message": "missing"},
                    {"severity": "error", "code": "missing_attestation_screenshot", "message": "missing"},
                ],
            },
        )
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-validation.latest.json", {"summary": {"critical": 0, "error": 0, "warning": 0}})
        _write_json(root / "runtime" / "receipts" / "validation" / "stack-warning-budget.latest.json", {"warning_count": 0})
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-05-12T00:00:00Z",
                "runs": [
                    {
                        "run_id": snapshot_run,
                        "repo_id": "fitness",
                        "scenario_id": "fitness.progression-pr-smoke",
                        "git_sha": "target-sha",
                        "promotion_generated_at": "2026-05-12T00:00:00Z",
                        "promotion_status": "manual_review",
                        "evidence_profile": "web_visual",
                        "waived_lanes": [],
                        "waiver_refs": [],
                        "receipt_origin": {
                            "origin_type": "local_dev",
                            "actor": "atlas-local",
                            "workflow_name": "",
                            "workflow_run_id": "",
                            "command": "python ops/atlas/qa/promote_run.py",
                            "runner_os": "Windows",
                            "generated_at": "2026-05-12T00:00:00Z",
                            "repo": "fitness",
                            "git_sha": "target-sha",
                            "stack_lock_hash": "sha256:" + ("a" * 64),
                            "qa_runner_version": "atlas.qa.promote-run.v3",
                        },
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": snapshot_run,
                        "last_git_sha": "target-sha",
                        "last_promotion_status": "manual_review",
                        "last_promotion_display_status": "manual_review",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                        "receipt_origin_type": "local_dev",
                        "waived_lanes": [],
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "require_trusted_origin": True,
                        "allowed_release_origins": ["ci_release", "protected_manual", "provider"],
                        "allowed_pr_origins": ["ci_pr", "local_dev"],
                        "enforcement_stage": "warn",
                        "mode_requirements": {"release": {"allowed_statuses": ["promoted_physical_manual"]}},
                    }
                },
                "repo_overrides": {"fitness": {"release_profile": "release_critical_web"}},
            },
        )
        self._write_stack_lock(root=root, components={"fitness": "target-sha"})
        build_release_readiness(root=root)
        result = build_release_snapshot(root=root, repo_id="fitness")
        payload = load_json_object(root / result["snapshot_summary_ref"])
        self.assertEqual(
            [
                "android.chrome.emulated",
                "desktop.chromium.emulated",
                "desktop.chromium.real.manual",
                "iphone.webkit.emulated",
            ],
            payload["evidence_present"],
        )
        self.assertEqual(
            ["android.chrome.real.manual", "iphone.webkit.real.manual"],
            payload["evidence_missing"],
        )

    def test_adoption_drift_detects_stale_and_missing_docs(self) -> None:
        root = self._temp_root()
        (root / "repos" / "fawxzzy-fitness" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "fawxzzy-fitness" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        _write_json(
            root / "repos" / "fawxzzy-fitness" / "qa" / "adapters" / "fitness.web.json",
            {
                "contract_version": "atlas.qa.adapter.v1",
                "adapter_id": "fitness.web",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "framework": "nextjs",
                "start": {"kind": "dev_server", "command": "npm run dev", "cwd": "repos/fawxzzy-fitness", "ready_url": "http://127.0.0.1:3000"},
                "capture": {"tool": "playwright"},
                "lenses": [],
            },
        )
        _write_json(
            root / "repos" / "fawxzzy-fitness" / "qa" / "scenarios" / "fitness.progression-pr-smoke.json",
            {
                "contract_version": "atlas.qa.scenario.v1",
                "scenario_id": "fitness.progression-pr-smoke",
                "title": "Fitness smoke",
                "repo_id": "fitness",
                "repo_path": "repos/fawxzzy-fitness",
                "adapter_id": "fitness.web",
                "criticality": "high",
                "entrypoint": {"route": "/", "ready_selector": "body"},
                "promotion": {"require_real_device_on": "release"},
            },
        )
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {"display_name": "Release-Critical Web"},
                    "web_visual": {"display_name": "Web Visual"},
                },
                "repo_overrides": {"fitness": {"release_profile": "release_critical_web"}},
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "runs": [
                    {
                        "run_id": "fitness-run",
                        "repo_id": "fitness",
                        "promotion_generated_at": "2000-01-01T00:00:00Z",
                    }
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_promotion_status": "manual_review",
                        "last_promotion_display_status": "manual_review",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )
        result = build_adoption_drift(root=root, max_receipt_age_hours=1)
        self.assertTrue((root / result["adoption_drift_ref"]).exists())
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "adoption-drift.latest.json")
        repo = payload["repos"][0]
        self.assertEqual("drift", repo["status"])
        self.assertIn("missing docs/qa.md", repo["findings"])

    def test_adoption_drift_labels_prototype_only_root_config(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        _write_json(root / "ops" / "atlas" / "qa" / "adapters" / "stream.package.json", {"repo_id": "stream"})
        _write_json(root / "ops" / "atlas" / "qa" / "scenarios" / "stream.contract-smoke.json", {"repo_id": "stream"})
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        _write_json(root / "ops" / "atlas" / "qa" / "release_policy.v1.json", {"contract_version": "atlas.qa.release_policy.v1", "profiles": {}, "repo_overrides": {}})
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "runs": [],
                "adoption": [],
                "summary": {},
                "retention": {},
            },
        )
        build_adoption_drift(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "adoption-drift.latest.json")
        self.assertEqual(["stream"], payload["summary"]["prototype_only_repos"])
        self.assertEqual("prototype_only_root_config", payload["prototype_only"][0]["disposition"])

    def test_adoption_drift_uses_repo_registry_for_root_owned_docs_path(self) -> None:
        root = self._temp_root()
        (root / "repos" / "playbook" / "docs").mkdir(parents=True, exist_ok=True)
        (root / "repos" / "playbook" / "docs" / "qa.md").write_text("# qa\n", encoding="utf-8")
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "adapters").mkdir(parents=True, exist_ok=True)
        (root / "ops" / "atlas" / "qa" / "scenarios").mkdir(parents=True, exist_ok=True)
        (root / "stack.yaml").write_text(
            "\n".join(
                [
                    "repo_registry:",
                    "  playbook:",
                    "    path: repos/playbook",
                    "    role: docs",
                    "    status: active",
                ]
            ) + "\n",
            encoding="utf-8",
        )
        _write_json(root / "ops" / "atlas" / "qa" / "adapters" / "playbook.docs.json", {"repo_id": "playbook"})
        _write_json(root / "ops" / "atlas" / "qa" / "scenarios" / "playbook.docs-governance.json", {"repo_id": "playbook"})
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {"docs_governance": {"display_name": "Docs Governance"}},
                "repo_overrides": {"playbook": {"release_profile": "docs_governance"}},
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": "2026-05-11T00:00:00Z",
                "runs": [{"run_id": "playbook-run", "repo_id": "playbook", "promotion_generated_at": "2026-05-11T00:00:00Z"}],
                "adoption": [
                    {
                        "repo_id": "playbook",
                        "adopted": True,
                        "owner": "playbook",
                        "adapter_refs": ["ops/atlas/qa/adapters/playbook.docs.json"],
                        "scenario_refs": ["ops/atlas/qa/scenarios/playbook.docs-governance.json"],
                        "evidence_profile": "docs_governance",
                        "last_run_id": "playbook-run",
                        "last_promotion_status": "promoted_emulated",
                        "last_promotion_display_status": "promoted_docs_governance",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    }
                ],
                "summary": {},
                "retention": {},
            },
        )

        build_adoption_drift(root=root)
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "adoption-drift.latest.json")
        repo = payload["repos"][0]
        self.assertEqual("repos/playbook/docs/qa.md", repo["docs_ref"])
        self.assertTrue(repo["docs_present"])

    def test_release_rehearsal_reflects_ready_blocked_and_not_applicable_repos(self) -> None:
        root = self._temp_root()
        (root / "ops" / "atlas" / "qa").mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        (root / "stack.lock.yaml").write_text(
            "\n".join(
                [
                    'schema_version: "atlas.stack.lock.v1"',
                    "components:",
                    "  fitness:",
                    '    commit: "fitness-sha"',
                    "    release_eligible: true",
                    "  playbook:",
                    '    commit: "playbook-sha"',
                    "    release_eligible: true",
                    "  stream:",
                    '    commit: "stream-sha"',
                    "    release_eligible: false",
                    "    remote: null",
                ]
            ) + "\n",
            encoding="utf-8",
        )
        _write_json(
            root / "ops" / "atlas" / "qa" / "release_policy.v1.json",
            {
                "contract_version": "atlas.qa.release_policy.v1",
                "profiles": {
                    "release_critical_web": {
                        "display_name": "Release-Critical Web",
                        "mode_requirements": {"release": {"allowed_statuses": ["promoted_physical_manual"]}},
                    },
                    "docs_governance": {
                        "display_name": "Docs Governance",
                        "mode_requirements": {"release": {"allowed_statuses": ["promoted_emulated"]}},
                    },
                    "package_contract": {
                        "display_name": "Package Contract",
                        "require_trusted_origin": True,
                        "enforcement_stage": "enforce",
                        "allowed_release_origins": ["protected_manual"],
                        "mode_requirements": {"release": {"allowed_statuses": ["promoted_emulated"]}},
                    },
                },
                "repo_overrides": {
                    "fitness": {"release_profile": "release_critical_web"},
                    "playbook": {"release_profile": "docs_governance"},
                    "stream": {"release_profile": "package_contract"},
                },
            },
        )
        _write_json(
            root / "runtime" / "atlas" / "qa" / "evidence-index.latest.json",
            {
                "contract_version": "atlas.qa.evidence_index.v1",
                "generated_at": generated_at,
                "runs": [
                    {"run_id": "fitness-run", "repo_id": "fitness", "git_sha": "fitness-sha", "promotion_generated_at": generated_at},
                    {"run_id": "playbook-run", "repo_id": "playbook", "git_sha": "playbook-sha", "promotion_generated_at": generated_at},
                    {"run_id": "stream-run", "repo_id": "stream", "git_sha": "stream-sha", "promotion_generated_at": generated_at, "receipt_origin": {"origin_type": "local_dev"}},
                ],
                "adoption": [
                    {
                        "repo_id": "fitness",
                        "adopted": True,
                        "owner": "fitness",
                        "adapter_refs": ["repos/fawxzzy-fitness/qa/adapters/fitness.web.json"],
                        "scenario_refs": ["repos/fawxzzy-fitness/qa/scenarios/fitness.progression-pr-smoke.json"],
                        "evidence_profile": "web_visual",
                        "last_run_id": "fitness-run",
                        "last_git_sha": "fitness-sha",
                        "last_promotion_status": "manual_review",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    },
                    {
                        "repo_id": "playbook",
                        "adopted": True,
                        "owner": "playbook",
                        "adapter_refs": ["repos/fawxzzy-playbook/qa/adapters/playbook.docs.json"],
                        "scenario_refs": ["repos/fawxzzy-playbook/qa/scenarios/playbook.docs-governance.json"],
                        "evidence_profile": "docs_governance",
                        "last_run_id": "playbook-run",
                        "last_git_sha": "playbook-sha",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    },
                    {
                        "repo_id": "stream",
                        "adopted": True,
                        "owner": "stream",
                        "adapter_refs": ["repos/stream/qa/adapters/stream.package.json"],
                        "scenario_refs": ["repos/stream/qa/scenarios/stream.contract-smoke.json"],
                        "evidence_profile": "package_contract",
                        "last_run_id": "stream-run",
                        "last_git_sha": "stream-sha",
                        "last_promotion_status": "promoted_emulated",
                        "root_runner_version": "atlas.qa.evaluate-run.v2",
                        "contract_version": "atlas.qa.promotion.v1",
                    },
                ],
                "summary": {},
                "retention": {},
            },
        )
        result = build_release_rehearsal(root=root)
        self.assertTrue((root / result["release_rehearsal_ref"]).exists())
        payload = load_json_object(root / "runtime" / "atlas" / "qa" / "release-rehearsal.latest.json")
        repos = {item["repo_id"]: item for item in payload["repos"]}
        self.assertEqual("fail", repos["fitness"]["readiness_status"])
        self.assertEqual("pass", repos["playbook"]["readiness_status"])
        self.assertEqual("not_applicable", repos["stream"]["readiness_status"])
        self.assertEqual(1, payload["summary"]["not_applicable_count"])


if __name__ == "__main__":
    unittest.main()
