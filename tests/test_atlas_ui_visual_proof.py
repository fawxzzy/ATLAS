from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ops.atlas.ui_visual_proof.fitness import (
    UI_VISUAL_PROOF_CONTRACT_VERSION,
    default_schema_path,
    run_visual_proof,
    validate_schema_definition,
    validate_visual_proof_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def _digest(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _png(path: Path, color: tuple[int, int, int, int], *, changed_pixels: set[tuple[int, int]] | None = None) -> None:
    image = Image.new("RGBA", (4, 4), color)
    for x, y in changed_pixels or set():
        image.putpixel((x, y), (255, 0, 0, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def _mask(path: Path, *, allowed_pixels: set[tuple[int, int]]) -> None:
    image = Image.new("L", (4, 4), 0)
    for x, y in allowed_pixels:
        image.putpixel((x, y), 255)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def write_visual_proof_fixture_stack(root: Path) -> tuple[Path, dict]:
    capture_map = {
        "contract_version": "atlas.ui.capture-map.v1",
        "owner_repo_id": "fitness",
        "owner_repo_path": "repos/fawxzzy-fitness",
        "captures": [
            {
                "capture_id": "proof-a",
                "screen_key": "proof",
                "screen_label": "Proof",
                "state_key": "a",
                "state_label": "A",
                "route_family": "proof",
                "owner_surface_refs": ["repos/fawxzzy-fitness/src/app/proof-a.tsx"],
                "primitive_variants": {
                    "header": {"primitive_id": "header", "variant_id": "shared"},
                    "card": {"primitive_id": "card", "variant_id": "panel"},
                    "tag": {"primitive_id": "badge", "variant_id": "default"},
                    "section_layout": {"primitive_id": "section-layout", "variant_id": "standard"},
                },
            },
            {
                "capture_id": "proof-b",
                "screen_key": "proof",
                "screen_label": "Proof",
                "state_key": "b",
                "state_label": "B",
                "route_family": "proof",
                "owner_surface_refs": ["repos/fawxzzy-fitness/src/app/proof-b.tsx"],
                "primitive_variants": {
                    "header": {"primitive_id": "header", "variant_id": "shared"},
                    "card": {"primitive_id": "card", "variant_id": "panel"},
                    "tag": {"primitive_id": "badge", "variant_id": "default"},
                    "section_layout": {"primitive_id": "section-layout", "variant_id": "standard"},
                },
            },
        ],
    }
    capture_map_path = root / "ops" / "atlas" / "ui_observe" / "fitness_capture_map.v1.json"
    capture_map_path.parent.mkdir(parents=True, exist_ok=True)
    capture_map_path.write_text(json.dumps(capture_map, indent=2) + "\n", encoding="utf-8")

    (root / "repos" / "fawxzzy-fitness" / "src" / "app").mkdir(parents=True, exist_ok=True)
    (root / "repos" / "fawxzzy-fitness" / "src" / "app" / "proof-a.tsx").write_text("// fixture\n", encoding="utf-8")
    (root / "repos" / "fawxzzy-fitness" / "src" / "app" / "proof-b.tsx").write_text("// fixture\n", encoding="utf-8")

    observation_root = root / "runtime" / "atlas" / "ui-observe" / "fitness"
    for capture_id in ("proof-a", "proof-b"):
        payload = {
            "contract_version": "atlas.ui.observation.v1",
            "capture": {"capture_id": capture_id},
            "comparison_digest": f"sha256:{capture_id.rjust(64, '0')[-64:]}",
        }
        target = observation_root / capture_id / "latest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "contract_version": UI_VISUAL_PROOF_CONTRACT_VERSION,
        "owner_repo_id": "fitness",
        "owner_repo_path": "repos/fawxzzy-fitness",
        "capture_map_ref": "ops/atlas/ui_observe/fitness_capture_map.v1.json",
        "expected_capture_map_digest": _digest(capture_map),
        "image_artifact_root": "runtime/atlas/ui-observe/fitness",
        "reference_root": "data/atlas/ui-visual-proof/fitness",
        "captures": [],
    }
    manifest_path = root / "ops" / "atlas" / "ui_visual_proof" / "fitness_visual_proof.v1.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path, capture_map


class AtlasUiVisualProofTests(unittest.TestCase):
    def test_schema_definition_is_valid(self) -> None:
        schema = json.loads(default_schema_path(ROOT).read_text(encoding="utf-8"))
        self.assertEqual([], validate_schema_definition(schema))

    def test_repo_manifest_validates(self) -> None:
        manifest_path = ROOT / "ops" / "atlas" / "ui_visual_proof" / "fitness_visual_proof.v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual([], validate_visual_proof_manifest(manifest, root=ROOT))

    def test_repo_manifest_only_gates_current_deterministic_visual_lane(self) -> None:
        manifest_path = ROOT / "ops" / "atlas" / "ui_visual_proof" / "fitness_visual_proof.v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        capture_ids = [item["capture_id"] for item in manifest["captures"]]

        self.assertEqual(
            [
                "settings-overview-default",
                "today-overview-default",
                "routines-overview-default",
                "history-sessions-list-default",
                "history-exercises-default",
                "workout-card-session-summary-card",
                "detail-support-exercise-info-sheet",
            ],
            capture_ids,
        )
        self.assertFalse(any(capture_id.startswith("history-log-") for capture_id in capture_ids))

    def test_repo_manifest_reuses_existing_exercise_family_capture_ids(self) -> None:
        manifest_path = ROOT / "ops" / "atlas" / "ui_visual_proof" / "fitness_visual_proof.v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        captures_by_id = {item["capture_id"]: item for item in manifest["captures"]}

        self.assertIn("history-exercises-default", captures_by_id)
        self.assertIn("detail-support-exercise-info-sheet", captures_by_id)
        self.assertEqual({"kind": "unchanged"}, captures_by_id["history-exercises-default"]["assertion"])
        self.assertEqual(
            {"kind": "unchanged"},
            captures_by_id["detail-support-exercise-info-sheet"]["assertion"],
        )
        self.assertFalse(any(capture_id.startswith("exercise-detail-") for capture_id in captures_by_id))

    def test_repo_manifest_reuses_existing_main_tab_capture_ids_for_shared_nav(self) -> None:
        manifest_path = ROOT / "ops" / "atlas" / "ui_visual_proof" / "fitness_visual_proof.v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        captures_by_id = {item["capture_id"]: item for item in manifest["captures"]}

        for capture_id in (
            "today-overview-default",
            "routines-overview-default",
            "history-sessions-list-default",
            "history-exercises-default",
            "settings-overview-default",
        ):
            self.assertIn(capture_id, captures_by_id)
            self.assertEqual({"kind": "unchanged"}, captures_by_id[capture_id]["assertion"])

        self.assertFalse(any(capture_id.startswith("main-tab-") for capture_id in captures_by_id))

    def test_repo_manifest_reuses_existing_history_capture_ids_for_shared_history_chrome(self) -> None:
        manifest_path = ROOT / "ops" / "atlas" / "ui_visual_proof" / "fitness_visual_proof.v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        captures_by_id = {item["capture_id"]: item for item in manifest["captures"]}

        for capture_id in (
            "history-sessions-list-default",
            "history-exercises-default",
        ):
            self.assertIn(capture_id, captures_by_id)
            self.assertEqual({"kind": "unchanged"}, captures_by_id[capture_id]["assertion"])

        self.assertFalse(any(capture_id.startswith("history-shared-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("history-control-") for capture_id in captures_by_id))
        self.assertFalse(any(capture_id.startswith("history-log-") for capture_id in captures_by_id))

    def test_manifest_validation_accepts_declared_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path, _ = write_visual_proof_fixture_stack(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["captures"] = [{"capture_id": "proof-a", "assertion": {"kind": "unchanged"}}]
            self.assertEqual([], validate_visual_proof_manifest(manifest, root=root))

    def test_unchanged_capture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path, _ = write_visual_proof_fixture_stack(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["captures"] = [{"capture_id": "proof-a", "assertion": {"kind": "unchanged"}}]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            _png(root / "runtime" / "atlas" / "ui-observe" / "fitness" / "proof-a" / "visual" / "latest.png", (0, 0, 0, 255))
            _png(root / "data" / "atlas" / "ui-visual-proof" / "fitness" / "proof-a" / "reference.png", (0, 0, 0, 255))

            report = run_visual_proof(root=root, manifest_path=manifest_path, schema_path=default_schema_path(ROOT))
            self.assertEqual("clean", report["summary"]["status"])
            self.assertEqual(1, report["summary"]["passing_count"])

    def test_changed_only_within_mask_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path, _ = write_visual_proof_fixture_stack(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["captures"] = [{"capture_id": "proof-a", "assertion": {"kind": "changed_only_within_mask"}}]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            _png(root / "runtime" / "atlas" / "ui-observe" / "fitness" / "proof-a" / "visual" / "latest.png", (0, 0, 0, 255), changed_pixels={(1, 1)})
            _png(root / "data" / "atlas" / "ui-visual-proof" / "fitness" / "proof-a" / "reference.png", (0, 0, 0, 255))
            _mask(root / "data" / "atlas" / "ui-visual-proof" / "fitness" / "proof-a" / "mask.png", allowed_pixels={(1, 1)})

            report = run_visual_proof(root=root, manifest_path=manifest_path, schema_path=default_schema_path(ROOT))
            self.assertEqual("clean", report["summary"]["status"])
            self.assertEqual(0, report["results"][0]["metrics"]["outside_mask_diff_pixels"])

    def test_unexpected_diff_outside_mask_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path, _ = write_visual_proof_fixture_stack(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["captures"] = [{"capture_id": "proof-a", "assertion": {"kind": "changed_only_within_mask"}}]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            _png(root / "runtime" / "atlas" / "ui-observe" / "fitness" / "proof-a" / "visual" / "latest.png", (0, 0, 0, 255), changed_pixels={(2, 2)})
            _png(root / "data" / "atlas" / "ui-visual-proof" / "fitness" / "proof-a" / "reference.png", (0, 0, 0, 255))
            _mask(root / "data" / "atlas" / "ui-visual-proof" / "fitness" / "proof-a" / "mask.png", allowed_pixels={(1, 1)})

            report = run_visual_proof(root=root, manifest_path=manifest_path, schema_path=default_schema_path(ROOT))
            self.assertEqual("proof_failed", report["summary"]["status"])
            self.assertGreater(report["results"][0]["metrics"]["outside_mask_diff_pixels"], 0)

    def test_missing_reference_image_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path, _ = write_visual_proof_fixture_stack(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["captures"] = [{"capture_id": "proof-a", "assertion": {"kind": "unchanged"}}]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            _png(root / "runtime" / "atlas" / "ui-observe" / "fitness" / "proof-a" / "visual" / "latest.png", (0, 0, 0, 255))

            report = run_visual_proof(root=root, manifest_path=manifest_path, schema_path=default_schema_path(ROOT))
            self.assertEqual("proof_failed", report["summary"]["status"])
            self.assertEqual("Reference image is missing.", report["results"][0]["message"])

    def test_stale_manifest_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path, _ = write_visual_proof_fixture_stack(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expected_capture_map_digest"] = "sha256:" + ("f" * 64)
            manifest["captures"] = [{"capture_id": "proof-a", "assertion": {"kind": "unchanged"}}]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            _png(root / "runtime" / "atlas" / "ui-observe" / "fitness" / "proof-a" / "visual" / "latest.png", (0, 0, 0, 255))
            _png(root / "data" / "atlas" / "ui-visual-proof" / "fitness" / "proof-a" / "reference.png", (0, 0, 0, 255))

            report = run_visual_proof(root=root, manifest_path=manifest_path, schema_path=default_schema_path(ROOT))
            self.assertEqual("proof_failed", report["summary"]["status"])
            self.assertTrue(report["results"][0]["stale_manifest"])

    def test_cli_exits_non_zero_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path, _ = write_visual_proof_fixture_stack(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expected_capture_map_digest"] = "sha256:" + ("e" * 64)
            manifest["captures"] = [{"capture_id": "proof-a", "assertion": {"kind": "unchanged"}}]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python",
                    str(ROOT / "ops" / "atlas" / "ui_visual_proof" / "fitness.py"),
                    "--root",
                    str(root),
                    "--manifest-file",
                    str(manifest_path),
                    "--schema-file",
                    str(default_schema_path(ROOT)),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, completed.returncode)


if __name__ == "__main__":
    unittest.main()
