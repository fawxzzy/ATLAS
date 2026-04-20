from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.atlas.ui_observe.drift import (
    UI_DRIFT_REPORT_CONTRACT_VERSION,
    default_drift_schema_path,
    validate_drift_report_payload,
    validate_drift_schema_definition,
    validate_fitness_ui_drift,
)
from ops.atlas.ui_observe.fitness import (
    default_capture_map_schema_path,
    default_schema_path,
    observe_fitness_ui,
)
from tests.test_atlas_ui_observe import write_fixture_stack

ROOT = Path(__file__).resolve().parents[1]


class AtlasUiDriftTests(unittest.TestCase):
    def test_default_drift_schema_validates(self) -> None:
        schema = json.loads(default_drift_schema_path(ROOT).read_text(encoding="utf-8"))
        self.assertEqual([], validate_drift_schema_definition(schema))

    def test_validator_is_clean_for_compliant_observations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture_stack(root)
            observe_fitness_ui(
                root=root,
                schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                output_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
            )

            report = validate_fitness_ui_drift(
                root=root,
                observation_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
                report_root=root / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness",
                schema_path=default_drift_schema_path(ROOT),
                observation_schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                dry_run=True,
            )

            self.assertEqual(UI_DRIFT_REPORT_CONTRACT_VERSION, report["contract_version"])
            self.assertEqual([], validate_drift_report_payload(report))
            self.assertEqual("clean", report["summary"]["status"])
            self.assertEqual(0, report["summary"]["finding_count"])

    def test_validator_detects_seeded_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_fixture_stack(root)
            observe_fitness_ui(
                root=root,
                schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                output_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
            )

            latest_path = (
                root
                / "runtime"
                / "atlas"
                / "ui-observe"
                / "fitness"
                / "today-overview-default"
                / "latest.json"
            )
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
            payload["traits"]["section_layout"]["variant_id"] = "drifted"
            payload["traits"]["section_layout"]["token_refs"] = ["spacing.99"]
            latest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            report = validate_fitness_ui_drift(
                root=root,
                observation_root=root / "runtime" / "atlas" / "ui-observe" / "fitness",
                report_root=root / "runtime" / "atlas" / "ui-observe" / "drift" / "fitness",
                schema_path=default_drift_schema_path(ROOT),
                observation_schema_path=default_schema_path(ROOT),
                capture_map_schema_path=default_capture_map_schema_path(ROOT),
                dry_run=True,
            )

            self.assertEqual("drift_detected", report["summary"]["status"])
            self.assertGreater(report["summary"]["finding_count"], 0)
            self.assertTrue(any(item["dimension"] == "section_layout" for item in report["findings"]))


if __name__ == "__main__":
    unittest.main()
