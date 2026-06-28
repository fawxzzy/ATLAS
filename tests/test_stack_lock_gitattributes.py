from __future__ import annotations

import unittest
from pathlib import Path


class StackLockGitAttributesTests(unittest.TestCase):
    def test_stack_lock_is_pinned_to_lf(self) -> None:
        root = Path(__file__).resolve().parents[1]
        lines = (root / ".gitattributes").read_text(encoding="utf-8").splitlines()
        normalized = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
        self.assertIn("stack.lock.yaml text eol=lf", normalized)
