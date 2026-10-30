"""Unit tests for AC15's non-secret, static source inventory."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ac15_source_inventory import build_inventory


class SourceInventoryTests(unittest.TestCase):
    """Ensure the inventory reports exposure indicators without secrets."""

    def test_identifies_surfaces_without_values(self) -> None:
        """Report risk categories and locations, never credential strings."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts/sage").mkdir(parents=True)
            (root / ".github/workflows").mkdir(parents=True)
            (root / "scripts/sage/example.py").write_text(
                "import os\nimport subprocess\n"
                "token = os.environ['GH_TOKEN']\n"
                "subprocess.run(['echo', 'dummy'])\n",
                encoding="utf-8",
            )
            (root / ".github/workflows/build.yml").write_text(
                "permissions:\n  contents: write\n"
                "env:\n  TOKEN: ${{ secrets.DONT_PRINT_THIS }}\n",
                encoding="utf-8",
            )
            audit = build_inventory(root)
            self.assertFalse(audit["runtime_isolation_verified"])
            self.assertEqual(audit["counts"]["ambient-environment-reference"], 1)
            self.assertEqual(audit["counts"]["subprocess-execution"], 1)
            self.assertEqual(audit["counts"]["actions-write-permission"], 1)
            self.assertNotIn("DONT_PRINT_THIS", str(audit))
            self.assertNotIn("GH_TOKEN", str(audit))

    def test_no_findings_does_not_assert_isolation(self) -> None:
        """Do not equate a clean source scan with runtime credential safety."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts/sage").mkdir(parents=True)
            (root / ".github/workflows").mkdir(parents=True)
            audit = build_inventory(root)
            self.assertEqual(audit["findings"], [])
            self.assertTrue(audit["non_exhaustive"])
            self.assertFalse(audit["live_github_permission_denial_verified"])


if __name__ == "__main__":
    unittest.main()
