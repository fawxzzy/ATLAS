from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ops.cortex._artifacts import write_json, write_json_if_changed


class CortexArtifactSerializationTests(unittest.TestCase):
    def test_write_json_uses_exact_utf8_lf_bytes_and_creates_parent(self) -> None:
        payload = {"message": "caf\u00e9", "values": [1, 2]}
        expected = json.dumps(payload, indent=2).encode("utf-8") + b"\n"

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "nested" / "artifact.json"

            write_json(path, payload)

            first = path.read_bytes()
            self.assertEqual(expected, first)
            self.assertTrue(first.endswith(b"\n"))
            self.assertFalse(first.endswith(b"\n\n"))
            self.assertNotIn(b"\r\n", first)

            write_json(path, payload)
            self.assertEqual(first, path.read_bytes())

    def test_write_json_if_changed_normalizes_crlf_once(self) -> None:
        payload = {"enabled": True, "schemas": ["public", "extensions"]}
        expected = json.dumps(payload, indent=2).encode("utf-8") + b"\n"
        crlf_equivalent = expected.replace(b"\n", b"\r\n")

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "artifact.json"
            path.write_bytes(crlf_equivalent)

            self.assertTrue(write_json_if_changed(path, payload))
            normalized = path.read_bytes()
            self.assertEqual(expected, normalized)
            self.assertNotIn(b"\r\n", normalized)

            self.assertFalse(write_json_if_changed(path, payload))
            self.assertEqual(normalized, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
